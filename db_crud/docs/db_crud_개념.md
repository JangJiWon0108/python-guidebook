# DB CRUD 개념 정리

FastAPI + SQLModel 기반 DB 연동 개념.
실제 프로젝트 (`metaadmin`) 코드 기반으로 파악.
경로 : \\wsl.localhost\Ubuntu\home\n-rda1\sunil_meta_server_real_and_cicd\local_code\data\metaadmin\app\backend\app

---

## 1. ORM 이란?

**Object Relational Mapping** — DB 테이블을 Python 클래스로 다루는 것.

```python
# SQL 직접 작성
SELECT * FROM user WHERE email = 'hong@test.com'

# ORM 방식 (SQLAlchemy / SQLModel)
session.exec(select(User).where(User.email == 'hong@test.com'))
```

SQL 을 직접 작성하지 않고 Python 코드로 DB 를 조작할 수 있음.

---

## 2. SQLAlchemy

Python 에서 가장 많이 쓰이는 ORM 라이브러리.

- DB 테이블 ↔ Python 클래스 매핑
- SQL 쿼리를 Python 코드로 작성
- MySQL, PostgreSQL, SQLite 등 다양한 DB 지원
- `engine` : DB 연결 객체
- `Session` : 트랜잭션 단위 (쿼리 실행 컨텍스트)

---

## 3. SQLModel

SQLAlchemy + Pydantic 을 합친 라이브러리. FastAPI 와 궁합이 좋음.

| | SQLAlchemy | SQLModel |
|--|--|--|
| 역할 | ORM | SQLAlchemy + Pydantic 합친 것 |
| 모델 정의 | `Base` 상속 | `SQLModel` 상속 |
| 타입 검증 | 없음 | Pydantic 기반 자동 검증 |
| FastAPI 궁합 | 보통 | 매우 좋음 |

SQLModel 은 SQLAlchemy 를 내부적으로 사용하는 래퍼.

```python
# SQLAlchemy 방식
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)

# SQLModel 방식 (현재 프로젝트)
class User(SQLModel, table=True):
    __tablename__ = "user"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
```

`table=True` → 실제 DB 테이블로 매핑. 없으면 Pydantic 모델로만 동작.

---

## 4. 전체 구조 및 흐름

```
라우터 (routes/users.py)
  ↓ SessionDep (Depends 로 자동 주입)
deps.py → get_db() → Session 생성
  ↓
crud/users.py → 실제 쿼리 실행
  ↓
schema.py → DB 테이블 모델 (User)
  ↓
core/db.py → engine (DB 연결)
  ↓
PostgreSQL
```

---

## 5. 각 파일 역할

### schema.py — DB 테이블 모델

```python
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class User(SQLModel, table=True):
    __tablename__ = "user"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    hashed_password: str = Field()
    full_name: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
```

- `table=True` : 실제 DB 테이블과 매핑
- `Field(primary_key=True)` : PK 지정
- `Field(unique=True)` : 유니크 제약
- `Field(index=True)` : 인덱스 생성 (조회 성능 향상)

---

### core/db.py — DB 연결 (engine)

```python
from sqlmodel import create_engine, Session

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
# SQLALCHEMY_DATABASE_URI 예시: postgresql://user:pass@host:5432/dbname
```

- `engine` : DB 연결 풀을 관리하는 객체
- 앱 시작 시 1번만 생성, 전역으로 사용

---

### api/deps.py — Session 주입 (Depends)

```python
from collections.abc import Generator
from sqlmodel import Session
from fastapi import Depends
from typing import Annotated

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session   # 요청마다 세션 생성 → 완료 후 자동 닫힘

# 라우터에서 타입힌트로 사용
SessionDep = Annotated[Session, Depends(get_db)]
```

- `yield` : 제너레이터로 세션 생성 → 요청 완료 후 `with` 블록 종료 → 세션 자동 닫힘
- `Depends(get_db)` : FastAPI 가 요청마다 자동으로 세션을 만들어서 주입
- `SessionDep` : 라우터 파라미터 타입힌트로 사용

---

### crud/users.py — 실제 쿼리

```python
from sqlmodel import Session, select, col, func

# 전체 조회
def get_users(session: Session, skip: int = 0, limit: int = 50) -> list[User]:
    stmt = select(User).order_by(User.email).offset(skip).limit(limit)
    return list(session.exec(stmt).all())

# 카운트
def count_users(session: Session) -> int:
    stmt = select(func.count()).select_from(User)
    return session.exec(stmt).one()

# 단건 조회 (PK)
def get_user(session: Session, user_id: UUID) -> User | None:
    return session.get(User, user_id)

# 단건 조회 (조건)
def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()

# 생성
def create_user(session: Session, email: str, password: str) -> User:
    user = User(email=email, hashed_password=get_password_hash(password))
    session.add(user)      # 변경사항 등록
    session.commit()       # DB 에 반영
    session.refresh(user)  # DB 에서 최신 상태 재조회 (id 등 채워짐)
    return user

# 수정
def update_user(session: Session, user: User, email: str | None = None) -> User:
    if email is not None:
        user.email = email
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# 삭제
def delete_user(session: Session, user: User) -> None:
    session.delete(user)
    session.commit()
```

**핵심 패턴:**

| 메서드 | 역할 |
|--|--|
| `session.exec(select(...))` | SELECT 쿼리 실행 |
| `session.get(Model, id)` | PK 로 단건 조회 |
| `session.add(obj)` | INSERT / UPDATE 등록 |
| `session.commit()` | DB 에 반영 |
| `session.refresh(obj)` | DB 에서 최신 상태 재조회 |
| `session.delete(obj)` | DELETE 등록 |

---

### routes/users.py — 라우터에서 사용

```python
from app.api.deps import SessionDep
from app.crud import users as crud_users

@router.get("/")
def list_users(session: SessionDep):       # SessionDep → 자동으로 세션 주입
    return crud_users.get_users(session)

@router.post("/")
def create_user(session: SessionDep, user: UserCreate):
    return crud_users.create_user(session, email=user.email, password=user.password)
```

---

## 6. Session 과 트랜잭션

```
요청 시작
  ↓
get_db() → Session 생성 (트랜잭션 시작)
  ↓
session.add() / session.exec() ...
  ↓
session.commit() → DB 반영
  ↓
요청 완료 → with 블록 종료 → Session 자동 닫힘
```

- `commit()` 전에 오류 발생 → 자동 롤백
- 세션은 요청 1개당 1개 생성, 요청 완료 후 닫힘

---

## 7. 정리

```
SQLAlchemy   →  Python ORM 의 핵심 라이브러리
SQLModel     →  SQLAlchemy + Pydantic 합친 것 (FastAPI 최적화)
engine       →  DB 연결 풀 (앱 시작 시 1번 생성)
Session      →  트랜잭션 단위 (요청마다 생성/종료)
schema.py    →  DB 테이블 = Python 클래스
crud/*.py    →  쿼리 로직 분리
deps.py      →  Depends 로 세션 자동 주입
```
