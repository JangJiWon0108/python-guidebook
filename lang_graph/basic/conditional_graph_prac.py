# LangGraph 조건부 분기(conditional edge) 실습
# state 값에 따라 다음에 실행할 노드를 다르게 선택한다

from typing import TypedDict

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    number: int
    result: str


# 분기 지점 역할만 하는 통과용 노드 (state 변경 없음)
def check(state: State) -> State:
    print(f"check 실행 - number : {state['number']}")
    return {}


# 라우팅 함수 : state를 보고 다음 노드 이름(문자열)을 반환
def route(state: State) -> str:
    if state["number"] % 2 == 0:
        return "even"
    return "odd"


def even_node(state: State) -> State:
    return {"result": f"{state['number']} 는 짝수"}


def odd_node(state: State) -> State:
    return {"result": f"{state['number']} 는 홀수"}


graph = StateGraph(State)
graph.add_node("check", check)
graph.add_node("even", even_node)
graph.add_node("odd", odd_node)

graph.add_edge(START, "check")

# check 노드 실행 후, route() 반환값에 따라 even/odd 노드로 분기
graph.add_conditional_edges(
    "check",
    route,
    {"even": "even", "odd": "odd"},
)

graph.add_edge("even", END)
graph.add_edge("odd", END)

app = graph.compile()

if __name__ == "__main__":
    for n in [4, 7, 10, 3]:
        result = app.invoke({"number": n, "result": ""})
        print(f"결과 : {result}\n")
