# FastAPI Docker 가이드

참고: https://fastapi.tiangolo.com/deployment/docker/
현재 프로젝트 기반 (uv + uvicorn 방식) 으로 작성.

---

## 1. 기본 개념

- **컨테이너 이미지** : 앱 실행에 필요한 코드, 의존성, 설정을 패키징한 파일
- **컨테이너** : 이미지를 실행한 인스턴스
- VM 과 달리 호스트 OS 커널을 공유 → 가볍고 빠름

> 공식 문서에서 `tiangolo/uvicorn-gunicorn-fastapi` 베이스 이미지는 **더 이상 권장하지 않음**.
> Python 공식 이미지에서 직접 빌드하는 것이 권장 방식.

---

## 2. 현재 프로젝트 구조

```
python-study/                  ← 빌드 컨텍스트 루트
├── pyproject.toml             ← 의존성 정의
├── uv.lock                    ← 의존성 잠금 파일
└── fast_api/
    ├── Dockerfile
    ├── .dockerignore
    ├── main.py
    ├── routers/
    │   ├── __init__.py
    │   ├── user_router.py
    │   └── cpu_router.py
    └── schemas/
        ├── __init__.py
        └── user_schema.py
```

`pyproject.toml`, `uv.lock` 이 루트에 있으므로 **빌드 컨텍스트는 `python-study/` 루트** 기준.

---

## 3. Dockerfile

`fast_api/Dockerfile`

```dockerfile
# 베이스 이미지
FROM python:3.12-slim

# uv 설치 (공식 이미지에서 바이너리만 복사 - pip install 보다 가볍고 빠름)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 앱 전체 복사
COPY . /app

# 의존성 설치
WORKDIR /app
RUN uv sync --frozen --no-cache

# uvicorn 직접 실행 (exec form - SIGTERM 신호가 프로세스에 직접 전달됨)
CMD ["/app/.venv/bin/uvicorn", "fast_api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
```

### CMD exec form vs shell form

```dockerfile
# exec form (권장) - SIGTERM 이 uvicorn 프로세스에 직접 전달 → 정상 종료
CMD ["/app/.venv/bin/uvicorn", "fast_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# shell form (비권장) - /bin/sh -c 를 거쳐 실행 → SIGTERM 전달 안 됨 → 강제 종료
CMD /app/.venv/bin/uvicorn fast_api.main:app --host 0.0.0.0 --port 8000
```

### 로컬 vs 도커 실행 방식 차이

| | 로컬 | 도커 |
|--|--|--|
| 실행 명령 | `uv run -m fast_api.main` | `uvicorn fast_api.main:app` |
| `__main__` 실행 | O | X (uvicorn 이 import 해서 실행) |
| uvicorn.run() | main.py 안에서 실행 | CMD 에서 직접 uvicorn 실행 |

로컬에서는 `uv run -m` 으로 `if __name__ == "__main__"` 을 통해 `uvicorn.run()` 이 실행됨.
도커에서는 uvicorn 이 `fast_api.main` 을 **import** 해서 `app` 객체를 가져오므로 `__main__` 블록이 실행되지 않음.
따라서 도커 CMD 에 uvicorn 명령을 직접 써줘야 함.

---

## 4. .dockerignore

```
.venv
__pycache__
*.pyc
.git
fast_api/docs/
```

---

## 5. 레이어 캐시 전략

Docker 는 각 명령어를 레이어로 저장하고, 변경이 없으면 캐시를 재사용한다.
의존성 파일을 먼저 복사하면 코드만 바뀔 때 `uv sync` 레이어를 재사용할 수 있음.

```dockerfile
# 의존성 파일 먼저 복사 (자주 안 바뀜 → 캐시 재사용)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# 앱 코드 복사 (자주 바뀜 → 캐시 무효화되어도 uv sync 는 재실행 안 함)
COPY fast_api/ ./fast_api/
```

---

## 6. 이미지 빌드

```bash
# python-study/ 루트에서 실행
docker build -t jangjiwon/fastapi-docker-prac -f fast_api/Dockerfile .

# 절대경로로도 가능 (어느 위치에서 실행하든 동일)
docker build -t jangjiwon/fastapi-docker-prac \
  -f /home/n-rda1/python-study/fast_api/Dockerfile \
  /home/n-rda1/python-study/
```

### 이미지 태그 구조

```
jangjiwon / fastapi-docker-prac : latest
    ↑               ↑               ↑
 계정명           이미지명        버전태그 (생략 시 latest 자동)
```

`docker push jangjiwon/fastapi-docker-prac` 하면 Docker Hub 의 해당 계정에 업로드됨.

### 빌드 컨텍스트

`COPY . /app` 이 빌드 컨텍스트 기준으로 복사하므로 컨텍스트 경로가 중요함.
반드시 특정 위치에서 실행해야 하는 건 아니고, **Dockerfile 이 참조하는 파일들이 컨텍스트 안에 있으면** 됨.

---

## 7. 컨테이너 실행

```bash
docker run -d --name fastapi-container -p 8000:8000 jangjiwon/fastapi-docker-prac
```

- `-d` : 백그라운드 실행
- `--name` : 컨테이너 이름
- `-p 8000:8000` : 호스트 8000포트 → 컨테이너 8000포트

---

## 8. 확인 및 테스트

```bash
# 실행 중인 컨테이너 확인
docker ps

# 로그 확인 (-f : 실시간 follow)
docker logs -f fastapi-container

# 이벤트루프 테스트
for i in {1..4}; do curl -s http://localhost:8000/users/$i/$i & done; wait

# 워커 테스트
for i in {1..4}; do curl -s http://localhost:8000/cpu/task & done; wait
```

---

## 9. 정지 및 삭제

```bash
docker stop fastapi-container         # 컨테이너 정지
docker rm fastapi-container           # 컨테이너 삭제
docker rmi jangjiwon/fastapi-docker-prac  # 이미지 삭제
```

---

## 10. 워커 테스트 (workers=1 vs workers=4)

Dockerfile CMD 의 `--workers` 값을 바꿔서 재빌드 후 비교.

### workers=1 실제 결과

```
INFO:     Started server process [1]        ← 도커 컨테이너 안 PID 는 1부터 시작
INFO:     Uvicorn running on http://0.0.0.0:8000

[07:46:19] [PID 1] cpu_task 시작
[07:46:21] [PID 1] cpu_task 완료 - 2.71초, CPU 6.7%   ← 끝나야 다음 시작
[07:46:21] [PID 1] cpu_task 시작
[07:46:24] [PID 1] cpu_task 완료 - 2.84초, CPU 7.4%
[07:46:24] [PID 1] cpu_task 시작
[07:46:27] [PID 1] cpu_task 완료 - 2.91초, CPU 9.6%
[07:46:27] [PID 1] cpu_task 시작
[07:46:30] [PID 1] cpu_task 완료 - 2.9초, CPU 8.8%
```

- PID 전부 `1` → 프로세스 1개, 순차 처리
- 총 약 **11초** (2.71 + 2.84 + 2.91 + 2.9)
- CPU 약 **6~9%**

> 도커 컨테이너 안에서는 PID 가 1부터 시작함. 로컬과 달리 격리된 PID 네임스페이스를 사용하기 때문.

---

### workers=4

Dockerfile CMD 수정 후 재빌드:

```dockerfile
CMD ["/app/.venv/bin/uvicorn", "fast_api.main:app",
     "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```bash
docker stop fastapi-container && docker rm fastapi-container
docker build -t jangjiwon/fastapi-docker-prac -f fast_api/Dockerfile .
docker run -d --name fastapi-container -p 8000:8000 jangjiwon/fastapi-docker-prac

for i in {1..4}; do curl -s http://localhost:8000/cpu/task & done; wait
```

실제 결과:
```
INFO:     Started parent process [1]
INFO:     Started server process [10]   ← 워커 4개
INFO:     Started server process [9]
INFO:     Started server process [8]
INFO:     Started server process [11]

[07:50:57] [PID 10] cpu_task 시작
[07:50:57] [PID 8]  cpu_task 시작      ← PID 각각 다름, 동시 시작
[07:50:57] [PID 11] cpu_task 시작
[07:50:57] [PID 9]  cpu_task 시작
[07:51:00] [PID 10] cpu_task 완료 - 3.61초, CPU 26.5%
[07:51:00] [PID 8]  cpu_task 완료 - 3.66초, CPU 26.5%
[07:51:00] [PID 11] cpu_task 완료 - 3.67초, CPU 26.4%
[07:51:00] [PID 9]  cpu_task 완료 - 3.69초, CPU 26.4%
```

- PID 8, 9, 10, 11 각각 다름 → 프로세스 4개, 병렬 처리
- 총 약 **3.7초**
- CPU 약 **26%** (코어 4개 분산)

---

### 비교

| | workers=1 | workers=4 |
|--|--|--|
| PID | 전부 `1` | 8, 9, 10, 11 각각 다름 |
| 처리 방식 | 순차 | 병렬 |
| 총 소요 시간 | ~11초 | ~3.7초 |
| CPU 사용률 | ~6~9% | ~26% |
| 프로세스 수 | 1개 | 부모 1 + 워커 4 = 5개 |

---

## 11. uvicorn CMD 옵션 정리

| 옵션 | 설명 |
|--|--|
| `--host 0.0.0.0` | 모든 네트워크 인터페이스에서 접근 허용 |
| `--port 8000` | 컨테이너 내부 포트 |
| `--workers N` | 워커(프로세스) 수 |
| `--proxy-headers` | Nginx 등 리버스 프록시 헤더 신뢰 |
