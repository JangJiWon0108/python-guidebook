# LangGraph Plan-and-Execute(Planner) 패턴 실습
#
# 구조 : Planner -> (Executor -> Replanner) 반복 -> Respond
# - Planner   : 사용자 목표를 단계별 계획(Plan)으로 쪼갬
# - Executor  : 계획의 첫 번째 단계를 하나 실행하고 결과를 past_steps에 누적
# - Replanner : 남은 단계가 있으면 계속 실행(CONTINUE), 없으면 종료(DONE) 판단
# - Respond   : past_steps를 근거로 최종 응답 생성
#
# 실제 서비스에서는 ChatOpenAI/ChatAnthropic 등 진짜 LLM을 쓰지만,
# 이 실습은 API 키 없이 오프라인으로 돌아가도록 langchain_core의
# FakeListChatModel로 LLM 자리를 대체했다.
# FakeListChatModel은 미리 정해둔 응답을 호출 순서대로 하나씩 반환하는
# 테스트용 모델이라, 이 스크립트의 정해진 흐름에서만 의미가 맞는다.
# (실제 LLM이라면 매번 state를 보고 스스로 판단해서 응답을 생성함)

import operator
from typing import Annotated, TypedDict

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field


# ==================== State ====================

class State(TypedDict):
    input: str
    plan: list[str]
    # operator.add 리듀서 : 매 execute마다 새 튜플을 "누적"시킴
    # (node가 [새_튜플] 을 반환하면 기존 리스트 뒤에 append 되듯 합쳐짐)
    past_steps: Annotated[list[tuple[str, str]], operator.add]
    response: str


# ==================== Planner ====================

class Plan(BaseModel):
    """사용자 목표를 달성하기 위한 순서가 있는 단계 목록"""
    steps: list[str] = Field(description="순서대로 실행할 단계 목록")


plan_parser = PydanticOutputParser(pydantic_object=Plan)

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 planner 입니다. 목표를 달성할 단계별 계획을 세우세요.\n{format_instructions}"),
    ("user", "{input}"),
])

# 실제 서비스라면 여기 대신 ChatOpenAI(model="gpt-4o") 등을 사용
planner_llm = FakeListChatModel(responses=[
    '{"steps": ["서울의 현재 인구를 조사한다", "부산의 현재 인구를 조사한다"]}',
])


def plan_step(state: State) -> State:
    chain = planner_prompt | planner_llm | plan_parser
    plan = chain.invoke({
        "input": state["input"],
        "format_instructions": plan_parser.get_format_instructions(),
    })
    print(f"[plan] 계획 수립 : {plan.steps}")
    return {"plan": plan.steps}


# ==================== Executor ====================

executor_llm = FakeListChatModel(responses=[
    "서울 인구 : 약 940만명",
    "부산 인구 : 약 330만명",
])


def execute_step(state: State) -> State:
    task = state["plan"][0]
    result = executor_llm.invoke(task).content
    print(f"[execute] '{task}' 실행 -> {result}")
    return {
        "plan": state["plan"][1:],          # 실행한 단계는 계획에서 제거
        "past_steps": [(task, result)],     # 리듀서(operator.add)가 자동으로 누적
    }


# ==================== Replanner ====================

replanner_llm = FakeListChatModel(responses=[
    "CONTINUE",  # 1번째 replan 시점 : 아직 부산 조사가 남음
    "DONE",      # 2번째 replan 시점 : 모든 단계 완료
])


def replan_step(state: State) -> State:
    decision = replanner_llm.invoke(
        f"남은 계획 : {state['plan']}, 지금까지 결과 : {state['past_steps']}"
    ).content
    print(f"[replan] 남은 계획 {state['plan']} -> 판단 : {decision}")
    # decision 자체는 state에 반영할 필요 없음 (라우팅에서만 사용)
    return {}


def route_after_replan(state: State) -> str:
    # 실제로는 replanner_llm의 텍스트 판단을 그대로 쓰겠지만,
    # 여기서는 그래프 라우팅 규칙을 명확히 보여주기 위해 plan 잔여 여부로 확정한다
    if state["plan"]:
        return "execute"
    return "respond"


# ==================== Respond ====================

respond_llm = FakeListChatModel(responses=[
    "서울 인구(약 940만명)가 부산 인구(약 330만명)보다 약 3배 많습니다.",
])


def respond_step(state: State) -> State:
    steps_summary = "\n".join(f"- {task}: {result}" for task, result in state["past_steps"])
    final = respond_llm.invoke(f"아래 조사 결과를 바탕으로 최종 답변을 작성해줘.\n{steps_summary}").content
    print(f"[respond] 최종 응답 생성")
    return {"response": final}


# ==================== Graph 조립 ====================

graph = StateGraph(State)
graph.add_node("plan", plan_step)
graph.add_node("execute", execute_step)
graph.add_node("replan", replan_step)
graph.add_node("respond", respond_step)

graph.add_edge(START, "plan")
graph.add_edge("plan", "execute")
graph.add_edge("execute", "replan")
graph.add_conditional_edges(
    "replan",
    route_after_replan,
    {"execute": "execute", "respond": "respond"},
)
graph.add_edge("respond", END)

app = graph.compile()


if __name__ == "__main__":
    result = app.invoke({
        "input": "서울과 부산의 인구를 비교해줘",
        "plan": [],
        "past_steps": [],
        "response": "",
    })

    print("\n" + "=" * 30)
    print(f"past_steps : {result['past_steps']}")
    print(f"최종 response : {result['response']}")
