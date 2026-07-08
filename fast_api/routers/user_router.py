from pickle import LIST
import asyncio
from datetime import datetime
# pyrefly: ignore [missing-import]
from fastapi import APIRouter
import time

from fast_api.schemas.user_schema import CreateUserReq, CreateUserRes, GetUserRes, GetUserByIdRes

# 라우터 정의
router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# 인메모리 db
inmemory_db = []

# 시간 return 함수
def ts():
    return datetime.now().strftime("[%H:%M:%S]")

# 테스트용 i/o 비동기 함수
async def test_async_f(
    user_id: int,
    delay: int
) -> list:
    print(f"{ts()} 비동기함수 시작 - id : {user_id}, delay : {delay}")
    await asyncio.sleep(delay)
    # time.sleep(delay)
    print(f"{ts()} 비동기함수 끝 - id : {user_id}, delay : {delay}")

    return [user_id, delay]

# POST /users [유저 등록]
@router.post("", response_model = CreateUserRes)
async def create_user(create_user_req: CreateUserReq) -> CreateUserRes:

    new_user = {
        "id" : len(inmemory_db) + 1,
        "name" : create_user_req.name,
        "age" : create_user_req.age
    }
    
    inmemory_db.append(new_user)
    
    return CreateUserRes(
        success = True,
        message = "유저 등록 성공",
        id = new_user["id"]
    )

# GET /users [유저 전체 조회]
@router.get("", response_model = GetUserRes)
async def get_users() -> GetUserRes:
    pass


# GET /user/{id} [특정 유저 조회]
@router.get("/{id}/{delay}", response_model = list)
async def get_user_by_id(id: int, delay: int) -> list:
    result_list = await test_async_f(id, delay)
    return result_list