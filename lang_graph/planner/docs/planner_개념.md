# Plan-and-Execute (Planner) 패턴

---

## 왜 필요한가?

가장 단순한 LLM 에이전트 방식인 **ReAct**(Thought → Action → Observation 반복)는 매 단계마다 LLM을 다시 호출해서 "다음에 뭘 할지"를 판단한다.

- 단계가 많아질수록 매번 큰 모델을 호출해야 해서 **느리고 비용이 많이 든다**
- 매 스텝마다 전체 맥락을 다시 판단하므로 **긴 작업일수록 일관성이 흔들리기 쉽다**

**Plan-and-Execute(Planner)** 패턴은 이를 개선하기 위해 역할을 나눈다.

- **Planner** : 큰 목표를 받아서 **한 번에** 여러 단계짜리 계획(Plan)을 세움 (똑똑하고 비싼 모델 1회 호출)
- **Executor** : 계획의 각 단계를 하나씩 실행 (가볍고 저렴한 모델 N회 호출 가능)
- **Replanner** : 실행 결과를 보고 남은 계획을 그대로 진행할지, 계획을 수정할지, 이제 끝내고 최종 응답을 줄지 판단

비용 구조로 보면 대략 `(강한 모델 1회) + (약한 모델 N회)` 라서, 단계 수(N)가 많아질수록 매번 강한 모델을 호출하는 ReAct보다 유리해진다.

---

## 전체 흐름

```
START -> plan -> execute -> replan -> (계획 남음) -> execute (반복)
                                     -> (계획 없음) -> respond -> END
```

1. `plan` : 사용자 입력을 받아 단계별 계획(`Plan`, 문자열 리스트) 생성
2. `execute` : 계획의 첫 번째 단계를 실행하고, 실행 결과를 `past_steps`에 누적
3. `replan` : 남은 계획이 있으면 `execute`로 되돌아가고, 없으면 `respond`로 이동
4. `respond` : 지금까지의 `past_steps`를 근거로 최종 응답 생성

---

## 코드 포인트

### 1. 구조화된 계획 생성 (Pydantic + OutputParser)

```python
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

class Plan(BaseModel):
    """사용자 목표를 달성하기 위한 순서가 있는 단계 목록"""
    steps: list[str] = Field(description="순서대로 실행할 단계 목록")

plan_parser = PydanticOutputParser(pydantic_object=Plan)
# plan_parser.get_format_instructions() 를 프롬프트에 넣어주면
# LLM이 이 스키마에 맞는 형식으로 응답하도록 유도할 수 있다
```

LLM의 출력은 기본적으로 텍스트이므로, "몇 단계로 이루어진 계획"처럼 구조가 있는 데이터가 필요하면 Pydantic 모델 + Parser 조합으로 파싱한다.

### 2. state 리듀서 (`Annotated[..., operator.add]`)

```python
import operator
from typing import Annotated, TypedDict

class State(TypedDict):
    past_steps: Annotated[list[tuple[str, str]], operator.add]
```

지금까지 `lang_graph/basic/`에서 본 노드들은 반환값을 state에 그대로 덮어썼다. 하지만 `past_steps`는 매 실행마다 **누적**되어야 한다.

- `Annotated[타입, 리듀서함수]` 로 필드를 선언하면, 노드가 반환한 값을 **리듀서 함수로 기존 값과 합쳐서** state에 반영한다
- `operator.add` 는 리스트 두 개를 `+` 로 이어붙이는 함수 → 노드가 `[새_항목]` 하나만 반환해도 기존 리스트 뒤에 자동으로 append 됨

### 3. 반복(loop) 구조

```python
graph.add_edge("execute", "replan")
graph.add_conditional_edges(
    "replan",
    route_after_replan,               # state를 보고 "execute" 또는 "respond" 반환
    {"execute": "execute", "respond": "respond"},
)
```

`조건부_분기.md`에서 다룬 `add_conditional_edges`를 활용하면, 조건에 따라 **이전 노드로 되돌아가는 반복 구조**도 그대로 만들 수 있다. (`replan` → 다시 `execute` 로)

---

## 이 실습에서 LLM을 실제로 호출하지 않는 이유

API 키 없이 오프라인에서도 실행/테스트가 가능해야 하므로, 실제 `ChatOpenAI`/`ChatAnthropic` 자리에 `langchain_core`의 `FakeListChatModel`을 사용했다.

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel

llm = FakeListChatModel(responses=["첫 번째 호출 응답", "두 번째 호출 응답"])
llm.invoke("아무 입력")  # 첫 번째 호출 -> "첫 번째 호출 응답"
llm.invoke("아무 입력")  # 두 번째 호출 -> "두 번째 호출 응답"
```

- `responses` 리스트에 미리 정해둔 답을 **호출된 순서대로** 그대로 반환하는 테스트용 모델
- 그래프의 노드 연결, 프롬프트 구성, structured output 파싱 등 나머지 코드는 실제 서비스와 동일한 방식
- **실제 서비스에서는 `planner_llm`/`executor_llm`/`replanner_llm`/`respond_llm` 자리를 진짜 LLM으로만 교체하면 됨**

## 실습 코드

- `planner_prac.py`

## 참고 자료

- [Plan-and-Execute Agents (LangChain Blog)](https://www.langchain.com/blog/planning-agents)
- [Plan-and-Execute - LangGraph 공식 튜토리얼](https://langchain-ai.github.io/langgraphjs/tutorials/plan-and-execute/plan-and-execute/)
