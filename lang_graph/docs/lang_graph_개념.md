# LangGraph 개념

---

## 왜 필요한가?

LLM에게 그냥 프롬프트 하나 던지고 끝나는 게 아니라, **여러 단계를 거치며 상태(state)를 주고받는 워크플로우**를 만들어야 할 때가 있다.

- 예: 질문 분류 → 조건에 따라 다른 처리 → 검증 → 재시도 → 최종 응답
- 이런 흐름을 `if/for`로 직접 짜면 분기가 늘어날수록 코드가 금방 스파게티가 된다

**LangGraph**는 이런 흐름을 **그래프(노드 + 엣지)** 로 표현하게 해주는 라이브러리다.

- 노드(Node) : 하나의 작업 단위 (함수)
- 엣지(Edge) : 노드 사이의 연결(순서)
- 상태(State) : 그래프 전체가 공유하며 노드를 거칠 때마다 갱신되는 데이터

내부적으로는 **상태 머신(state machine)** 이라고 보면 된다. LLM 호출이 꼭 들어가야 하는 건 아니라서, 이 문서의 예제들은 API 키 없이도 일반 파이썬 함수로 그래프 개념만 익히도록 구성했다.

---

## 핵심 구성 요소

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. State : 그래프 전체가 공유하는 데이터 구조 (TypedDict로 정의)
class State(TypedDict):
    count: int

# 2. Node : state를 받아서 갱신할 값을 dict로 반환하는 함수
def add_one(state: State) -> State:
    return {"count": state["count"] + 1}

# 3. Graph 생성 : State 타입을 넘겨서 StateGraph 생성
graph = StateGraph(State)

# 4. Node 등록
graph.add_node("add_one", add_one)

# 5. Edge 연결 : START(진입점) -> add_one -> END(종료점)
graph.add_edge(START, "add_one")
graph.add_edge("add_one", END)

# 6. compile() : 실행 가능한 앱으로 컴파일
app = graph.compile()

# 7. invoke() : state를 넣고 그래프 실행
result = app.invoke({"count": 0})
print(result)  # {'count': 1}
```

- `add_node(이름, 함수)` : 노드 등록. 함수는 state를 받아 **갱신할 부분만** dict로 반환
- `add_edge(from, to)` : 고정된 순서로 연결
- `START`, `END` : 그래프의 시작/끝을 나타내는 특수 노드
- `compile()` : 그래프를 실제 실행 가능한 객체로 변환 (변환 전엔 실행 불가)
- `invoke(state)` : 동기 실행, 최종 state 반환
- `stream(state)` : 각 노드를 거칠 때마다 중간 state를 스트리밍으로 받고 싶을 때 사용

---

## Node가 여러 개일 때 (순차 실행)

```python
class State(TypedDict):
    text: str

def step1(state: State) -> State:
    return {"text": state["text"] + " -> step1"}

def step2(state: State) -> State:
    return {"text": state["text"] + " -> step2"}

graph = StateGraph(State)
graph.add_node("step1", step1)
graph.add_node("step2", step2)

graph.add_edge(START, "step1")
graph.add_edge("step1", "step2")  # step1 다음 step2 실행
graph.add_edge("step2", END)

app = graph.compile()
print(app.invoke({"text": "시작"}))
# {'text': '시작 -> step1 -> step2'}
```

노드 함수는 **state 전체를 새로 만드는 게 아니라, 바뀐 필드만 반환**한다. 나머지 필드는 LangGraph가 알아서 기존 state와 merge 해준다.

---

## 다음 문서

- `조건부_분기.md` : state 값에 따라 다음 노드를 다르게 선택하는 conditional edge
- `checkpointer.md` : 그래프 실행 중간 상태를 저장하고 이어서 실행하는 메모리 기능

## 실습 코드

- `basic_graph_prac.py`
