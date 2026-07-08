# Deep Agent 패턴

---

## 왜 필요한가?

`planner/` 문서에서 다룬 Plan-and-Execute는 "계획 → 실행 → 재계획"으로 다단계 작업을 처리했다. 하지만 작업이 더 복잡해지면(예: 리서치, 코딩처럼 장시간 이어지는 작업) 몇 가지 문제가 더 생긴다.

- 조사한 내용을 전부 대화 기록(state)에 쌓으면 **컨텍스트가 금방 커지고 오염됨**
- 하위 작업의 세세한 시행착오까지 메인 에이전트가 다 들고 있으면 **정작 중요한 판단에 집중하기 어려움**
- 장시간 작업일수록 **지금 뭘 했고 뭐가 남았는지 추적**이 안 되면 흐름을 잃기 쉬움

LangChain이 제시한 **Deep Agent** 아키텍처(`deepagents` 패키지, 2026년 3월 공식 발표)는 이를 해결하기 위해 ReAct 루프에 4가지 요소를 추가한다.

---

## 4가지 핵심 요소

### 1. Planning Tool (Todo List)

- 메인 에이전트가 작업을 시작하기 전에 **명시적인 할 일 목록**을 만든다 (`write_todos` 도구)
- 실제로 뭔가를 실행하는 도구가 아니라, "지금 무엇을 하고 있고 무엇이 남았는지"를 계속 눈에 보이게 유지하는 역할 (일종의 no-op 도구)
- 장시간 작업일수록 일관성을 지키는 데 큰 효과가 있다고 알려짐

### 2. Sub-agent (컨텍스트 격리)

- 무거운 하위 작업(예: "OO 리서치해줘")은 **별도의 서브 에이전트**에게 통째로 위임한다
- 서브 에이전트가 내부적으로 몇 번을 시도하고 실패하든, 메인 에이전트는 그 과정을 전혀 보지 않고 **최종 결과만** 돌려받는다
- 메인 에이전트의 컨텍스트가 하위 작업의 잡음으로 오염되는 것을 막는 게 핵심 목적

### 3. Virtual Filesystem

- 조사 결과나 중간 산출물을 대화 기록에 계속 누적하는 대신, **가상의 "파일"** 로 저장한다
- 메인 에이전트는 필요할 때만 파일을 열어 보고, 평소엔 파일명/경로만 참조 → 컨텍스트 오프로드
- 실제 `deepagents` 패키지는 기본적으로 state(메모리)에 저장하지만, `FilesystemBackend` 등으로 실제 디스크에 연결할 수도 있음

### 4. 상세한 System Prompt

- 메인 에이전트와 서브 에이전트 각각에게 **역할과 행동 범위를 명확히 지정**하는 프롬프트를 준다
- "너는 무엇을 하는 존재고, 무엇을 하면 안 되는지"를 분명히 할수록 장시간 작업에서도 일관성이 유지됨

> 네 가지가 함께 동작하는 방식: Planning Tool이 진행 상황을 추적하고, Sub-agent가 전문화·격리를 담당하고, File System이 메모리 저장을 해결하고, System Prompt가 행동 경계를 정의한다.

---

## 이 실습의 흐름

```
START -> write_todos -> run_next_todo -> (todo 남음) -> run_next_todo (반복)
                                        -> (todo 없음) -> respond -> END
```

1. `write_todos` : 사용자 목표를 todo 목록으로 쪼갬 (Planning Tool)
2. `run_next_todo` : pending 상태인 todo 하나를 골라 **서브 에이전트(`run_subagent`)** 에 위임
   - 서브 에이전트는 해당 task 문자열만 받고, 메인 state는 전달받지 않음 → 컨텍스트 격리
   - 서브 에이전트의 결과는 대화 기록이 아니라 `state["files"]` (가상 파일)에 저장됨
   - todo 상태를 `completed`로 변경
3. 남은 pending todo가 있으면 `run_next_todo`를 반복, 없으면 `respond`로 이동
4. `respond` : 가상 파일시스템에 쌓인 내용을 근거로 최종 응답 생성

```python
def run_subagent(task: str) -> str:
    # 메인 그래프의 state를 넘기지 않고, task 문자열 하나만 전달 -> 컨텍스트 격리
    result = subagent_llm.invoke(f"{SUBAGENT_SYSTEM_PROMPT}\n작업 : {task}")
    return result.content

def run_next_todo(state: State) -> State:
    target = next(t for t in todos if t["status"] == "pending")
    result_text = run_subagent(target["content"])   # 서브 에이전트에 위임, 최종 결과만 수신

    filename = _todo_to_filename(target["content"])
    files = dict(state["files"])
    files[filename] = result_text                    # 가상 파일로 저장 (컨텍스트 오프로드)
    ...
```

---

## 실제 `deepagents` 패키지와의 차이

- 실제 [`deepagents`](https://github.com/langchain-ai/deepagents) 패키지는 `create_deep_agent()` 한 줄로 위 4가지 요소가 다 갖춰진 LangGraph 그래프를 만들어준다
- 다만 실제 tool-calling이 가능한 LLM(`ChatOpenAI` 등)이 필요해서 API 키 없이는 실행할 수 없다
- 이 실습은 **같은 4가지 개념을 순수 `StateGraph` + `FakeListChatModel`로 직접 구현**해서, API 키 없이도 구조를 눈으로 보고 실행/테스트할 수 있게 만든 버전이다
- 개념을 이해한 뒤 실제 서비스에 적용할 때는 `deepagents` 패키지의 `create_deep_agent()`를 사용하는 것이 더 실용적이다

## 실습 코드

- `deepagent_prac.py`

## 참고 자료

- [Deep Agents overview (LangChain 공식 문서)](https://docs.langchain.com/oss/python/deepagents/overview)
- [LangChain Deep Agents 소개](https://www.langchain.com/deep-agents)
- [GitHub - langchain-ai/deepagents](https://github.com/langchain-ai/deepagents)
- [DeepAgents Architecture: Planning Tools, Sub-agents, and File System](https://eastondev.com/blog/en/posts/ai/deepagents-architecture/)
