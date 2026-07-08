# FastAPI 와 async/await

코루틴(async/await) 을 학습한 뒤 FastAPI 를 이해하기 위한 문서.
FastAPI 는 코루틴 기반으로 동작하기 때문에, 코루틴 개념을 알면 FastAPI 의 동작 방식이 자연스럽게 이해된다.

---

## FastAPI 란?

Python 으로 만든 **웹 API 프레임워크**. REST API 서버를 빠르게 만들 수 있다.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users():
    return {"users": ["홍길동", "김철수"]}
```

---

## 주요 특징

**1. 빠른 성능**
- Node.js, Go 수준의 성능
- 비동기(async/await) 기반으로 동시 요청을 효율적으로 처리

**2. 자동 문서화**
- `/docs` 경로에 Swagger UI 자동 생성
- `/redoc` 경로에 ReDoc 자동 생성
- 코드만 작성하면 API 문서가 자동으로 만들어짐

**3. 타입 힌트 기반**
- Python 타입 힌트로 요청/응답 스펙을 정의
- Pydantic 으로 자동 유효성 검사

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str

@app.post("/users")
async def create_user(user: UserCreate):  # 타입 힌트로 자동 파싱 + 검증
    return user
```

---

## 구성 요소

```
FastAPI 앱
├── 라우터 (Router)   - URL 경로와 함수를 연결 (@app.get, @app.post 등)
├── 스키마 (Schema)   - 요청/응답 데이터 구조 정의 (Pydantic 모델)
├── 의존성 (Depends)  - 공통 로직 주입 (인증, DB 세션 등)
└── 미들웨어          - 요청/응답 전후 처리 (로깅, CORS 등)
```

---

## ASGI 란?

**ASGI (Asynchronous Server Gateway Interface)**
Python 웹 서버와 웹 프레임워크 사이의 표준 인터페이스.

```
클라이언트 → ASGI 서버 (uvicorn) → ASGI 앱 (FastAPI)
```

| | WSGI (구) | ASGI (신) |
|--|--|--|
| 방식 | 동기 (블로킹) | 비동기 (non-blocking) |
| 동시 요청 | 멀티프로세스/스레드 | 단일 이벤트루프 |
| 대표 서버 | gunicorn, uWSGI | uvicorn, hypercorn |
| 대표 프레임워크 | Flask, Django | FastAPI, Starlette |

---

## uvicorn 이란?

**uvicorn** : Python 용 고성능 ASGI 서버.

- 이벤트루프를 생성하고 관리
- HTTP 요청을 받아 FastAPI 앱에 전달
- 요청마다 라우터 함수를 task 로 등록

```bash
uvicorn main:app --reload
# main    : 파일명 (main.py)
# app     : FastAPI 인스턴스 변수명
# --reload: 코드 변경 시 자동 재시작 (개발용)
```

---

## 실행 방법

```bash
# 1. uvicorn 직접 실행 (세부 옵션 제어 가능)
uvicorn main:app --reload
uvicorn main:app --host 0.0.0.0 --port 8080

# 2. fastapi CLI (FastAPI 0.111.0+ 에서 추가된 래퍼)
fastapi dev main.py    # 개발모드 (--reload 자동, localhost 전용)
fastapi run main.py    # 프로덕션 모드

# 3. uv 로 실행
uv run uvicorn main:app --reload
uv run fastapi dev main.py
```

### fastapi run vs uvicorn 차이

| | `uvicorn main:app` | `fastapi run main.py` |
|--|--|--|
| 실체 | ASGI 서버 | uvicorn 을 감싼 CLI |
| 파일 지정 | `파일명:변수명` | `파일명.py` |
| 개발모드 | `--reload` 직접 지정 | `fastapi dev` 로 간단하게 |
| 옵션 | 세부 옵션 많음 | 간단하지만 제한적 |
| 도입 | - | FastAPI 0.111.0+ |

**결론:** 실행 결과는 동일. `fastapi run/dev` 는 편의를 위한 래퍼.

---

## 코루틴 개념 → FastAPI 대응

| 코루틴 개념 | FastAPI 대응 |
|--|--|
| `asyncio.run()` | uvicorn 이 이벤트루프 생성 및 실행 |
| 이벤트루프 | uvicorn 이 관리하는 이벤트루프 (1개) |
| `async def` 코루틴 함수 | `async def` 라우터 함수 |
| `asyncio.create_task()` | 요청이 올 때마다 라우터를 task 로 등록 |
| `await` | 라우터 안에서 DB/외부 API 호출 시 `await` |
| task 완료 | 라우터 처리 완료 → 클라이언트에 응답 반환 |
| 여러 task 동시 실행 | 여러 요청 동시 처리 |

---

## FastAPI 의 요청 처리 방식

FastAPI 는 ASGI 서버인 `uvicorn` 위에서 동작한다.
uvicorn 이 이벤트루프를 생성하고, 요청이 올 때마다 라우터 함수를 task 로 등록한다.

```
이벤트루프 (1개, uvicorn 이 생성 및 관리)
├── Task-1 (GET /users  요청1) → await DB → 일시정지
├── Task-2 (GET /users  요청2) → await DB → 일시정지  ← 같은 라우터도 별도 task
└── Task-3 (POST /items 요청3) → await DB → 일시정지
```

- 이벤트루프는 요청마다 새로 만드는 게 아니라 **하나만 존재**
- 요청마다 **task 가 생성**되어 이벤트루프에 등록됨
- 요청 단위 = 라우터 함수 호출 단위

---

## async def 라우터

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users():
    result = await db.query()  # DB I/O 대기 중 다른 요청 처리 가능
    return result
```

`await` 를 만나면 이벤트루프에 제어권을 넘기고, 다른 요청(task)이 실행된다.
DB 응답이 오면 다시 제어권을 받아서 응답을 반환한다.

---

## 동시 요청 처리 예시

`/users1`, `/users2`, `/users3` 에 동시에 요청이 오는 경우:

```python
@app.get("/users1")
async def get_users1():
    await db.query1()  # 1초

@app.get("/users2")
async def get_users2():
    await db.query2()  # 2초

@app.get("/users3")
async def get_users3():
    await db.query3()  # 3초
```

```
0s  요청1 → Task-1 등록 → query1() await → 일시정지
0s  요청2 → Task-2 등록 → query2() await → 일시정지
0s  요청3 → Task-3 등록 → query3() await → 일시정지

1s  Task-1 완료 → 요청1 응답 반환
2s  Task-2 완료 → 요청2 응답 반환
3s  Task-3 완료 → 요청3 응답 반환
```

| | 동기 (`def`) | 비동기 (`async def`) |
|--|--|--|
| 요청1 응답 | 1s | 1s |
| 요청2 응답 | 3s (1+2) | 2s |
| 요청3 응답 | 6s (1+2+3) | 3s |

---

## async def vs def 라우터

```python
# 비동기 - DB 대기 중 다른 요청 처리 가능
@app.get("/users")
async def get_users():
    await db.query()   # 이벤트루프에 제어권 넘김

# 동기 - DB 대기 중 이벤트루프 블로킹
@app.get("/users")
def get_users():
    db.query()         # 이 시간 동안 다른 요청 처리 못 함
```

> FastAPI 는 `def` 라우터도 지원한다. 내부적으로 별도 스레드에서 실행해서 이벤트루프가 블로킹되지 않도록 처리해준다. 하지만 DB/외부 API 같은 I/O 작업은 `async def` + `await` 를 쓰는 게 성능상 유리하다.

---

## 정리

```
uvicorn       →  이벤트루프 생성 및 관리
요청 1개      →  task 1개 생성
async def     →  코루틴 함수 (await 가능)
await         →  I/O 대기 중 제어권 넘김 → 다른 요청 처리
동시 요청     →  여러 task 가 이벤트루프에서 번갈아 실행
```
