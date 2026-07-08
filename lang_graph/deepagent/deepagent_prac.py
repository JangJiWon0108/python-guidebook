# Deep Agent 패턴 실습
#
# "Deep Agent" (LangChain의 deepagents 패키지가 제시하는 아키텍처)는
# 단순 ReAct 루프에 아래 4가지를 더한 구조다.
#
#   1. Planning Tool (todo list) : 작업을 명시적인 할 일 목록으로 쪼개서 추적
#   2. Sub-agent (context isolation) : 무거운 하위 작업은 별도 서브 에이전트에 위임하고,
#      메인 에이전트는 "최종 결과만" 돌려받아 컨텍스트 오염을 막음
#   3. Virtual Filesystem : 조사/작업 결과를 대화 기록에 쌓는 대신 "파일"로 저장해서
#      컨텍스트를 오프로드 (메인 state는 파일명만 참조)
#   4. 상세한 System Prompt : 각 에이전트(메인/서브)의 역할과 행동 범위를 명확히 지정
#
# 실제 deepagents 패키지는 진짜 tool-calling 가능한 LLM이 필요해서
# API 키 없이는 돌려볼 수 없다. 이 실습은 같은 4가지 개념을
# 순수 LangGraph(StateGraph) + FakeListChatModel 로 직접 구현해서
# 오프라인으로도 구조를 이해하고 실행/테스트할 수 있게 만든 버전이다.

from typing import TypedDict

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field


# ==================== 1. Planning Tool : Todo ====================

class Todo(TypedDict):
    content: str
    status: str  # "pending" | "completed"


class TodoList(BaseModel):
    """메인 에이전트가 세우는 할 일 목록"""
    todos: list[str] = Field(description="처리할 작업 목록")


class State(TypedDict):
    input: str
    todos: list[Todo]
    files: dict[str, str]   # 3. 가상 파일시스템 : 파일명 -> 내용
    response: str


MAIN_SYSTEM_PROMPT = (
    "당신은 메인 에이전트입니다. 사용자 목표를 받으면 먼저 todo 목록을 세우고, "
    "각 항목을 서브 에이전트에게 위임한 뒤, 그 결과를 파일로 저장하며 진행합니다."
)

todo_parser = PydanticOutputParser(pydantic_object=TodoList)

todo_prompt = ChatPromptTemplate.from_messages([
    ("system", MAIN_SYSTEM_PROMPT + "\n{format_instructions}"),
    ("user", "{input}"),
])

# 실제 서비스라면 이 자리에 진짜 LLM(ChatOpenAI 등)이 들어간다
planner_llm = FakeListChatModel(responses=[
    '{"todos": ["서울 여행 정보 조사", "부산 여행 정보 조사"]}',
])


def write_todos(state: State) -> State:
    """1. Planning Tool : 목표를 할 일 목록으로 쪼갠다 (deepagents의 write_todos 도구에 해당)"""
    chain = todo_prompt | planner_llm | todo_parser
    result = chain.invoke({
        "input": state["input"],
        "format_instructions": todo_parser.get_format_instructions(),
    })
    todos: list[Todo] = [{"content": t, "status": "pending"} for t in result.todos]
    print(f"[write_todos] 할 일 목록 생성 : {[t['content'] for t in todos]}")
    return {"todos": todos}


# ==================== 2. Sub-agent (컨텍스트 격리) ====================

SUBAGENT_SYSTEM_PROMPT = (
    "당신은 리서치 서브 에이전트입니다. 주어진 작업 하나만 조사하고, "
    "조사 과정은 노출하지 않고 최종 요약 결과만 반환하세요."
)

# 서브 에이전트 전용 LLM. 메인 에이전트의 대화 기록과 완전히 분리된 호출이라는 점이 핵심
# (실제로는 서브 에이전트가 자체적으로 여러 번 도구를 호출할 수도 있지만,
#  메인 에이전트 입장에서는 "최종 결과 한 덩어리"만 보인다)
subagent_llm = FakeListChatModel(responses=[
    "서울 : 경복궁, 남산타워, 광장시장이 대표 관광지. 지하철로 대부분 이동 가능",
    "부산 : 해운대, 감천문화마을, 자갈치시장이 대표 관광지. 바다 근처 숙소 추천",
])


def run_subagent(task: str) -> str:
    """서브 에이전트 호출. 메인 그래프의 state를 넘기지 않고, task 하나만 넘겨서
    컨텍스트를 격리한다. 반환값(최종 결과)만 메인 에이전트로 돌아온다."""
    result = subagent_llm.invoke(f"{SUBAGENT_SYSTEM_PROMPT}\n작업 : {task}")
    return result.content


# ==================== 3. 가상 파일시스템 ====================

def _todo_to_filename(content: str) -> str:
    return content.replace(" ", "_") + ".md"


def run_next_todo(state: State) -> State:
    """pending 상태인 todo를 하나 골라 서브 에이전트에게 위임하고,
    결과를 대화 기록이 아니라 가상 파일로 저장한다 (컨텍스트 오프로드)."""
    todos = [dict(t) for t in state["todos"]]
    target = next(t for t in todos if t["status"] == "pending")

    result_text = run_subagent(target["content"])

    filename = _todo_to_filename(target["content"])
    files = dict(state["files"])
    files[filename] = result_text

    target["status"] = "completed"
    print(f"[run_next_todo] '{target['content']}' 완료 -> {filename} 저장")

    return {"todos": todos, "files": files}


def route_after_todo(state: State) -> str:
    if any(t["status"] == "pending" for t in state["todos"]):
        return "run_next_todo"
    return "respond"


# ==================== 4. 최종 응답 (파일시스템 내용을 근거로) ====================

respond_llm = FakeListChatModel(responses=[
    "서울은 경복궁/남산타워/광장시장, 부산은 해운대/감천문화마을/자갈치시장을 중심으로 "
    "2박 3일 일정을 짜면 좋습니다. 자세한 내용은 seoul, busan 조사 파일을 참고하세요.",
])


def respond(state: State) -> State:
    """가상 파일시스템에 쌓인 결과들을 근거로 최종 응답을 만든다."""
    files_summary = "\n".join(f"[{name}]\n{content}" for name, content in state["files"].items())
    final = respond_llm.invoke(f"아래 파일들을 참고해서 최종 답변을 작성해줘.\n{files_summary}").content
    print("[respond] 최종 응답 생성")
    return {"response": final}


# ==================== Graph 조립 ====================

graph = StateGraph(State)
graph.add_node("write_todos", write_todos)
graph.add_node("run_next_todo", run_next_todo)
graph.add_node("respond", respond)

graph.add_edge(START, "write_todos")
graph.add_edge("write_todos", "run_next_todo")
graph.add_conditional_edges(
    "run_next_todo",
    route_after_todo,
    {"run_next_todo": "run_next_todo", "respond": "respond"},
)
graph.add_edge("respond", END)

app = graph.compile()


if __name__ == "__main__":
    result = app.invoke({
        "input": "서울과 부산 여행 계획을 세워서 도시별로 정리해줘",
        "todos": [],
        "files": {},
        "response": "",
    })

    print("\n" + "=" * 30)
    print(f"todos : {result['todos']}")
    print(f"files : {list(result['files'].keys())}")
    print(f"최종 response : {result['response']}")
