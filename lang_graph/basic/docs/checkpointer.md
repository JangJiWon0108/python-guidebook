# Checkpointer (상태 저장/이어서 실행)

---

## 왜 필요한가?

기본적으로 `app.invoke(state)`를 호출할 때마다 그래프는 **그 호출 안에서만** state를 들고 있다가 끝나면 사라진다.

- 챗봇처럼 "이전 대화 내용을 기억하고 이어서 응답" 해야 하는 경우
- 그래프 실행 도중 중단됐다가 나중에 이어서 실행해야 하는 경우

이럴 때 **checkpointer**를 붙이면, 그래프가 실행될 때마다 state를 저장소에 기록하고 `thread_id` 로 구분해서 이어 쓸 수 있다.

---

## 기본 사용법 (메모리 저장 - `MemorySaver`)

```python
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

# 1. checkpointer 준비 (여기서는 프로세스 메모리에만 저장 - 재시작하면 사라짐)
memory = MemorySaver()

# 2. compile 할 때 checkpointer 전달
app = graph.compile(checkpointer=memory)

# 3. thread_id로 대화/세션 구분
config = {"configurable": {"thread_id": "user-1"}}

print(app.invoke({"count": 0}, config=config))    # {'count': 1}
print(app.invoke({"count": 100}, config=config))  # {'count': 101}

# 4. 저장된 마지막 state 조회
snapshot = app.get_state(config)
print(snapshot.values)  # {'count': 101}
```

---

## 포인트

- `checkpointer`는 `compile(checkpointer=...)` 로 붙인다
- `thread_id`는 대화방/세션 하나를 구분하는 키다 — **다른 `thread_id`를 쓰면 완전히 별개의 state**로 취급됨
- `MemorySaver`는 프로세스가 꺼지면 데이터가 사라지는 **인메모리** 저장소. 실제 서비스에서는 SQLite/Postgres 등 영속 저장소용 checkpointer로 교체해서 사용함
- `app.get_state(config)` 로 특정 thread의 마지막 저장된 state를 조회할 수 있음

## 실습 코드

- `checkpoint_prac.py`
