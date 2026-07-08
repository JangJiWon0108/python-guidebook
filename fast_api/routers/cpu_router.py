import os
import time
import psutil
from datetime import datetime
# pyrefly: ignore [missing-import]
from fastapi import APIRouter

router = APIRouter(
    prefix="/cpu",
    tags=["cpu"]
)

def ts() -> str:
    return datetime.now().strftime("[%H:%M:%S]")

def heavy_compute(n: int) -> int:
    return sum(i * i for i in range(n))

@router.get("/task")
async def cpu_task():
    pid = os.getpid()

    print(f"{ts()} [PID {pid}] cpu_task 시작")

    cpu_before = psutil.cpu_percent(interval=None)
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