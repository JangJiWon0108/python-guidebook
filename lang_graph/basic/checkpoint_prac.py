# LangGraph checkpointer(MemorySaver) 실습
# thread_id 로 세션을 구분해서 이전 실행의 state를 저장/조회한다
# MemorySaver 는 프로세스 메모리에만 저장하므로, 스크립트가 끝나면 사라짐

from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


class State(TypedDict):
    count: int


def add_one(state: State) -> State:
    return {"count": state["count"] + 1}


graph = StateGraph(State)
graph.add_node("add_one", add_one)
graph.add_edge(START, "add_one")
graph.add_edge("add_one", END)

memory = MemorySaver()

# checkpointer를 붙여서 컴파일 -> 실행할 때마다 state가 저장됨
app = graph.compile(checkpointer=memory)

if __name__ == "__main__":
    config_user1 = {"configurable": {"thread_id": "user-1"}}
    config_user2 = {"configurable": {"thread_id": "user-2"}}

    print("=" * 30 + "\nuser-1 세션\n" + "=" * 30)
    print(app.invoke({"count": 0}, config=config_user1))
    print(app.invoke({"count": 100}, config=config_user1))

    print("\n" + "=" * 30 + "\nuser-2 세션 (user-1 과 완전히 별개)\n" + "=" * 30)
    print(app.invoke({"count": 0}, config=config_user2))

    print("\n" + "=" * 30 + "\n저장된 마지막 state 조회 (get_state)\n" + "=" * 30)
    print(f"user-1 마지막 state : {app.get_state(config_user1).values}")
    print(f"user-2 마지막 state : {app.get_state(config_user2).values}")
