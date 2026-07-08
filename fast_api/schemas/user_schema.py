# pyrefly: ignore [missing-import]
from pydantic import BaseModel

# user 관련 base 스키마
class UserBase(BaseModel):
    id: int
    name: str
    age: int

# POST /users (유저 등록)

# Request
class CreateUserReq(BaseModel):
    name: str
    age: int

# Response
class CreateUserRes(BaseModel):
    success: bool
    message: str
    id: int

# GET /users/{id} (유저 조회)

# response
class GetUserByIdRes(UserBase):
    success: bool
    message: str

# GET /users (유저 전체 조회)

# response
class GetUserRes(UserBase):
    success: bool
    message: str
    users: list[UserBase]