# LangGraph 기본 개념 실습
# State : 그래프 전체가 공유하는 데이터 (TypedDict로 정의)
# Node : state를 받아서, 바뀐 부분만 dict로 반환하는 함수
# Edge : 노드 사이의 실행 순서를 연결
# START/END : 그래프의 시작/끝을 나타내는 특수 노드

from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    text: str


# 노드 함수는 state를 받아, 갱신할 필드만 dict로 반환한다
# LangGraph가 반환값을 기존 state에 merge 해줌
def step1(state: State) -> State:
    print(f"step1 실행 - 입력 : {state['text']}")
    return {"text": state["text"] + " -> step1"}


def step2(state: State) -> State:
    print(f"step2 실행 - 입력 : {state['text']}")
    return {"text": state["text"] + " -> step2"}


def step3(state: State) -> State:
    print(f"step3 실행 - 입력 : {state['text']}")
    return {"text": state["text"] + " -> step3"}


# 1. State 타입을 넘겨서 그래프 생성
graph = StateGraph(State)

# 2. 노드 등록
graph.add_node("step1", step1)
graph.add_node("step2", step2)
graph.add_node("step3", step3)

# 3. 엣지로 순서 연결 : START -> step1 -> step2 -> step3 -> END
graph.add_edge(START, "step1")
graph.add_edge("step1", "step2")
graph.add_edge("step2", "step3")
graph.add_edge("step3", END)

# 4. 실행 가능한 앱으로 컴파일 (컴파일 전에는 invoke 불가)
app = graph.compile()

if __name__ == "__main__":
    print("\n" + "=" * 30 + "\ninvoke() : 최종 state만 한 번에 받기\n" + "=" * 30)
    result = app.invoke({"text": "시작"})
    print(f"\n최종 결과 : {result}")

    print("\n" + "=" * 30 + "\nstream() : 노드를 거칠 때마다 중간 state 받기\n" + "=" * 30)
    for chunk in app.stream({"text": "시작"}):
        print(chunk)
