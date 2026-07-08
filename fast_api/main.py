# pyrefly: ignore [missing-import]
import uvicorn
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from fast_api.routers import user_router, cpu_router

# fast api 객체 생성
app = FastAPI(
    title = "Jang",
    description = "Jang 설명",
    version = "1.0.0",
    docs_url = "/docs",
    redoc_url = "/redoc"
)

# 미들웨어
# CORS 미들웨어는 어플리케이션 레벨(브라우저 단) 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],      # 브라우저에서의 요청 허용할 주소 목록
    allow_methods = ["*"]       # 브라우저에서의 요청 허용할 메서드 목록
)

# 라우터
app.include_router(user_router.router)
app.include_router(cpu_router.router)

# main
# host 는 네트워크 레벨 설정
# 즉, 네트워크(3계층) -> 어플리케이션 (7계층) 
# 요청이 들어올 때는  1->7 순서로 가고, 응답이 나갈때는 7->1 순서로 감
# 요청을 예로 들면, host 에 허용되지 않은 주소 -> 차단 (cors 까지 안감)
# host에 허용된 주소 -> cors 에서도 허용 -> 최종 허용됨
# host에 허용된 주소 -> cors 에 허용x -> 차단
if __name__  == "__main__":
    uvicorn.run(
        "fast_api.main:app",                  # 파일명(uv run -m 하는 경로 기준):FastAPI 객체명
        host = "0.0.0.0",            # 어느 네트워크에서 요청을 받을지 (0.0.0.0 은 모든 네트워크 받음)
        port = 8000,                 # 포트
        workers = 2                # 워커 수 (프로세스 수) 설정
    )
