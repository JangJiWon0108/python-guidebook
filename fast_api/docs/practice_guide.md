# FastAPI 실습 가이드

동시 요청 처리를 직접 확인하는 실습.

---

## 1. 패키지 설치

```bash
# python-study/ 루트에서 실행
uv add fastapi uvicorn
```

---

## 2. 파일 구조

```
python-study/
└── fast_api/
    ├── main.py                  ← 앱 생성 + 미들웨어 + 라우터 등록 + uvicorn 실행
    ├── routers/
    │   ├── __init__.py
    │   └── user_router.py       ← /users 관련 라우터
    ├── schemas/
    │   ├── __init__.py
    │   └── user_schema.py       ← Pydantic 스키마 (요청/응답 형태)
    └── docs/
        └── practice_guide.md
```

### schemas vs models

| | schemas/ | models/ |
|--|--|--|
| 역할 | 요청/응답 데이터 형태 정의 | DB 테이블 정의 |
| 사용 | Pydantic | SQLAlchemy 등 ORM |
| 언제 | 항상 | DB 연결할 때 추가 |

---

## 3. schemas/user_schema.py

Pydantic 모델로 요청/응답 데이터 구조를 정의한다.
FastAPI 가 요청 body 를 자동으로 파싱/검증하고, 응답도 `response_model` 스키마로 자동 직렬화한다.

```python
from pydantic import BaseModel

# user 관련 base 스키마
class UserBase(BaseModel):
    id: int
    name: str
    age: int

# POST /users (유저 등록)
class CreateUserReq(BaseModel):   # 요청 - id 없음 (서버가 부여)
    name: str
    age: int

class CreateUserRes(BaseModel):   # 응답
    success: bool
    message: str
    id: int

# GET /users/{id} (유저 단건 조회)
class GetUserByIdRes(UserBase):   # UserBase 상속 (id, name, age 포함)
    success: bool
    message: str

# GET /users (유저 전체 조회)
class GetUserRes(UserBase):       # UserBase 상속
    success: bool
    message: str
    users: list[UserBase]
```

**요청/응답 분리 이유:**
- 요청(`CreateUserReq`) : id 없음 (서버가 부여하므로)
- 응답(`CreateUserRes`) : password 같은 민감정보 제외 가능

**빈값/누락 처리:**

| 케이스 | 결과 |
|--|--|
| `"name": ""` | 통과 (막으려면 `@field_validator` 추가) |
| `{}` 빈 body | 422 자동 반환 |
| 필드 누락 | 422 자동 반환 |

---

## 4. routers/user_router.py

```python
import asyncio
from datetime import datetime
from fastapi import APIRouter
from fast_api.schemas.user_schema import CreateUserReq, CreateUserRes, GetUserRes, GetUserByIdRes

router = APIRouter(prefix="/users", tags=["users"])

# prefix="/users" : 모든 라우터에 /users 자동 접두사
# tags=["users"]  : Swagger UI 에서 그룹핑

inmemory_db = []

def ts():
    return datetime.now().strftime("[%H:%M:%S]")

# I/O 비동기 시뮬레이션 함수
async def test_async_f(user_id: int, delay: int) -> list:
    print(f"{ts()} 비동기함수 시작 - id : {user_id}, delay : {delay}")
    await asyncio.sleep(delay)
    print(f"{ts()} 비동기함수 끝 - id : {user_id}, delay : {delay}")
    return [user_id, delay]

# POST /users
@router.post("", response_model=CreateUserRes)
async def create_user(create_user_req: CreateUserReq) -> CreateUserRes:
    new_user = {
        "id": len(inmemory_db) + 1,
        "name": create_user_req.name,   # .필드명 으로 접근
        "age": create_user_req.age
    }
    inmemory_db.append(new_user)
    return CreateUserRes(
        success=True,
        message="유저 등록 성공",
        id=new_user["id"]   # dict 이므로 ["키"] 로 접근
    )

# GET /users
@router.get("", response_model=GetUserRes)
async def get_users() -> GetUserRes:
    pass

# GET /users/{id}/{delay}
@router.get("/{id}/{delay}", response_model=list)
async def get_user_by_id(id: int, delay: int) -> list:
    result_list = await test_async_f(id, delay)
    return result_list
```

- `prefix` 가 `/users` 이므로 라우터 경로는 `""` 로 작성 (`"/"` 쓰면 `/users/` 로 등록돼 307 리다이렉트 발생)
- Pydantic 모델 필드 접근: `.필드명`
- dict 필드 접근: `["키"]`

---

## 5. main.py

```python
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fast_api.routers import user_router

app = FastAPI(
    title="Jang",
    description="Jang 설명",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 미들웨어 (7계층 - 애플리케이션 레벨, 브라우저 요청 제어)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # 허용할 브라우저 출처
    allow_methods=["*"]     # 허용할 HTTP 메서드
)

app.include_router(user_router.router)

# host 는 네트워크 레벨 (3계층) 설정
# 요청이 들어올 때: 1계층 → 7계층 순서
# host 차단 → CORS 까지 안 감
# host 허용 → CORS 에서 허용 → 최종 허용
# host 허용 → CORS 에서 차단 → 차단
if __name__ == "__main__":
    uvicorn.run(
        "fast_api.main:app",    # uv run -m 실행 경로 기준: 패키지명.파일명:FastAPI객체명
        host="0.0.0.0",         # 모든 네트워크 인터페이스에서 받음
        port=8000,
        # workers=1             # 워커 수 (프로세스 수)
    )
```

---

## 6. 서버 실행

```bash
# python-study/ 루트에서 실행
uv run -m fast_api.main
```

서버가 뜨면:
- `http://localhost:8000/docs` → Swagger UI
- `http://localhost:8000/redoc` → ReDoc

---

## 7. curl 테스트

### 유저 생성 (POST)

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "장지원", "age": 20}'
```

### 단건 조회 + 동시 요청 (GET /{id}/{delay})

`id` 와 `delay` 를 path parameter 로 받아 `delay` 초만큼 대기 후 응답.

```bash
# 단건
curl http://localhost:8000/users/1/1

# 반복문으로 동시 요청 (id=1~4, delay=id값)
for i in {1..4}; do
  curl -s http://localhost:8000/users/$i/$i &
done
wait
```

시간 측정 포함:

```bash
time (
  for i in {1..4}; do
    curl -s http://localhost:8000/users/$i/$i &
  done
  wait
)
```

- `$i` : 반복 변수 (1, 2, 3, 4)
- `&` : 백그라운드 실행 → 동시 요청
- `wait` : 전체 완료 대기

---

## 8. 동작 원리 — asyncio.sleep vs time.sleep 비교

### asyncio.sleep (비동기, 이벤트루프 제어권 양보)

실제 실행 결과:

```
[15:57:42] 비동기함수 시작 - id : 1, delay : 1
[15:57:42] 비동기함수 시작 - id : 2, delay : 2   ← 4개 거의 동시 시작
[15:57:42] 비동기함수 시작 - id : 3, delay : 3
[15:57:42] 비동기함수 시작 - id : 4, delay : 4

[15:57:43] 비동기함수 끝 - id : 1, delay : 1     ← 1초 후 완료
[15:57:44] 비동기함수 끝 - id : 2, delay : 2     ← 2초 후 완료
[15:57:45] 비동기함수 끝 - id : 3, delay : 3     ← 3초 후 완료
[15:57:46] 비동기함수 끝 - id : 4, delay : 4     ← 4초 후 완료
```

총 **4초** (가장 느린 것 기준). 4개 동시 처리.

```
0s  요청1 → await asyncio.sleep(1) → 이벤트루프에 제어권 넘김 → 일시정지
    요청2 → await asyncio.sleep(2) → 이벤트루프에 제어권 넘김 → 일시정지
    요청3 → await asyncio.sleep(3) → 이벤트루프에 제어권 넘김 → 일시정지
    요청4 → await asyncio.sleep(4) → 이벤트루프에 제어권 넘김 → 일시정지
1s  요청1 완료
2s  요청2 완료
3s  요청3 완료
4s  요청4 완료
```

---

### time.sleep (동기, 이벤트루프 블로킹)

`asyncio.sleep` → `time.sleep` 으로 바꾸면:

실제 실행 결과:

```
[15:59:50] 비동기함수 시작 - id : 2, delay : 2
[15:59:52] 비동기함수 끝 - id : 2, delay : 2     ← id:2 끝난 후
[15:59:52] 비동기함수 시작 - id : 1, delay : 1   ← id:1 시작
[15:59:53] 비동기함수 끝 - id : 1, delay : 1
[15:59:53] 비동기함수 시작 - id : 3, delay : 3
[15:59:56] 비동기함수 끝 - id : 3, delay : 3
[15:59:56] 비동기함수 시작 - id : 4, delay : 4
[16:00:00] 비동기함수 끝 - id : 4, delay : 4
```

총 **10초** (2+1+3+4). 순차 처리.

```
time.sleep() 은 이벤트루프 자체를 블로킹
→ await 를 써도 제어권을 넘기지 못함
→ 한 요청이 끝날 때까지 다른 요청 대기
```

---

### 비교 정리

| | `asyncio.sleep` | `time.sleep` |
|--|--|--|
| 이벤트루프 | 제어권 양보 → 다른 요청 처리 | 블로킹 → 다른 요청 대기 |
| 처리 방식 | 동시 | 순차 |
| 총 소요 시간 | 4초 (가장 느린 것) | 10초 (1+2+3+4) |
| 사용 상황 | I/O 대기 (DB, API 등) | 쓰면 안 됨 (async 함수 안에서) |

**핵심:** `async def` 안에서 `time.sleep()` 쓰면 비동기의 의미가 없어짐. 반드시 `await asyncio.sleep()` 사용.

---

## 9. 워커 실습 — CPU 작업에서 차이 체감

### 워커 구조

```
부모 프로세스 (parent process) - 요청 분배 + 워커 관리
├── 워커1 (server process) - 실제 요청 처리
├── 워커2 (server process)
├── 워커3 (server process)
└── 워커4 (server process)
```

- workers=4 → 총 **5개** 프로세스 (부모 1 + 워커 4)
- workers=1 → 총 **1개** 프로세스 (부모/워커 구분 없음)
- 부모 프로세스는 요청 분배 및 워커 생성/재시작만 담당, 실제 요청 처리는 안 함

실행 로그:
```
INFO: Started parent process [540936]    ← 부모 (관리자)
INFO: Started server process [541003]    ← 워커1
INFO: Started server process [541004]    ← 워커2
INFO: Started server process [541005]    ← 워커3
INFO: Started server process [541006]    ← 워커4
```

종료 시 부모가 워커들 먼저 종료 후 마지막에 자신이 종료:
```
INFO: Received SIGINT, exiting.
INFO: Waiting for child process [541003]
INFO: Waiting for child process [541004]
INFO: Waiting for child process [541005]
INFO: Waiting for child process [541006]
INFO: Stopping parent process [540936]
```

---

### routers/cpu_router.py

```python
import os
import time
import psutil
from datetime import datetime
from fastapi import APIRouter

router = APIRouter(prefix="/cpu", tags=["cpu"])

def ts() -> str:
    return datetime.now().strftime("[%H:%M:%S]")

def heavy_compute(n: int) -> int:
    return sum(i * i for i in range(n))

# async def 로 작성해야 이벤트루프에서 실행됨
# → workers 간 PID 차이가 명확하게 보임
# def 로 쓰면 FastAPI 가 스레드풀에서 실행 → 같은 프로세스 내 멀티스레드가 되어 PID 가 동일하게 나옴
@router.get("/task")
async def cpu_task():
    pid = os.getpid()
    print(f"{ts()} [PID {pid}] cpu_task 시작")

    psutil.cpu_percent(interval=None)   # 측정 기준점 초기화
    start = time.time()

    result = heavy_compute(2_000_0000)

    elapsed = round(time.time() - start, 2)
    cpu_after = psutil.cpu_percent(interval=None)

    print(f"{ts()} [PID {pid}] cpu_task 완료 - {elapsed}초, CPU {cpu_after}%")

    return {
        "pid": pid,
        "elapsed_sec": elapsed,
        "cpu_percent": cpu_after,
        "result": result
    }
```

- `async def` 사용 → 이벤트루프에서 실행 → 워커별 PID 차이 확인 가능
- `os.getpid()` : 어느 워커(프로세스)가 처리했는지 확인
- `psutil.cpu_percent()` : CPU 사용률 측정
- `uv add psutil` 설치 필요

---

### curl 명령

```bash
time (
  for i in {1..4}; do
    curl -s http://localhost:8000/cpu/task &
  done
  wait
)
```

---

### 실습 1 — workers=1

`main.py`:
```python
uvicorn.run("fast_api.main:app", host="0.0.0.0", port=8000, workers=1)
```

실제 결과:
```
[16:14:51] [PID 540555] cpu_task 시작
[16:14:53] [PID 540555] cpu_task 완료 - 2.13초, CPU 6.5%   ← 첫 번째 끝난 후
[16:14:53] [PID 540555] cpu_task 시작                       ← 두 번째 시작
[16:14:55] [PID 540555] cpu_task 완료 - 2.15초, CPU 6.4%
[16:14:55] [PID 540555] cpu_task 시작
[16:14:57] [PID 540555] cpu_task 완료 - 2.13초, CPU 6.6%
[16:14:57] [PID 540555] cpu_task 시작
[16:14:59] [PID 540555] cpu_task 완료 - 2.14초, CPU 6.4%
```
- PID 동일 → 프로세스 1개 순차 처리
- 총 약 **8초** (2.1 × 4)
- CPU 약 **6%** (코어 1개만 사용)

---

### 실습 2 — workers=4

`main.py`:
```python
uvicorn.run("fast_api.main:app", host="0.0.0.0", port=8000, workers=4)
```

실제 결과:
```
INFO:     Started parent process [540936]
INFO:     Started server process [541003]   ← 워커 4개 시작
INFO:     Started server process [541004]
INFO:     Started server process [541005]
INFO:     Started server process [541006]

[16:15:22] [PID 541006] cpu_task 시작
[16:15:22] [PID 541004] cpu_task 시작       ← 4개 동시 시작, PID 각각 다름
[16:15:22] [PID 541005] cpu_task 시작
[16:15:22] [PID 541003] cpu_task 시작
[16:15:25] [PID 541003] cpu_task 완료 - 2.45초, CPU 26.8%
[16:15:25] [PID 541006] cpu_task 완료 - 2.55초, CPU 26.6%
[16:15:25] [PID 541004] cpu_task 완료 - 2.56초, CPU 26.6%
[16:15:25] [PID 541005] cpu_task 완료 - 2.61초, CPU 26.2%
```
- PID 각각 다름 → 프로세스 4개 병렬 처리
- 총 약 **2.5초**
- CPU 약 **26%** (코어 4개 동시 사용)

---

### 실습 3 — workers=2

`main.py`:
```python
uvicorn.run("fast_api.main:app", host="0.0.0.0", port=8000, workers=2)
```

실제 결과:
```
INFO:     Started server process [541897]
INFO:     Started server process [541898]

[16:15:41] [PID 541897] cpu_task 시작
[16:15:41] [PID 541898] cpu_task 시작       ← 2개 동시 시작
[16:15:43] [PID 541898] cpu_task 완료 - 2.24초, CPU 13.2%
[16:15:43] [PID 541898] cpu_task 시작       ← 완료 즉시 나머지 처리
[16:15:43] [PID 541897] cpu_task 완료 - 2.3초, CPU 13.3%
[16:15:43] [PID 541897] cpu_task 시작
[16:15:45] [PID 541898] cpu_task 완료 - 2.17초, CPU 12.8%
[16:15:45] [PID 541897] cpu_task 완료 - 2.17초, CPU 12.7%
```
- PID 2개 → 2개씩 나눠서 처리
- 총 약 **4초** (2라운드)
- CPU 약 **13%** (코어 2개 사용)

---

### 실제 결과 비교

| workers | PID 수 | 처리 방식 | 총 소요 시간 | CPU 사용률 |
|--|--|--|--|--|
| 1 | 1개 | 순차 (4개 직렬) | ~8초 | ~6% |
| 2 | 2개 | 2개씩 병렬 | ~4초 | ~13% |
| 4 | 4개 | 전체 병렬 | ~2.5초 | ~26% |

워커가 늘수록 처리 시간은 줄고 CPU 사용률은 올라감.
