# 파이썬은 싱글스레드로 동작함. 그래서 대기 중에는 다른 작업을 못함
# 제너레이터로 해결 시도 : python 3.4 
## yield 가 함수 상태를 저장하고 멈출 수 있다는 것에 착안
## 대기 중에 yield 로 멈추고, 다른 함수를 실행하면 되지 않을까?
## Python 3.4에서 `@asyncio.coroutine` + `yield from` 으로 공식화
## 그러나 제너레이터와 같은 문법을 쓰므로 구분이 불가 등 여러 이유로 인해 3.5 부터 코루틴 등장
# 코루틴 등장 : python 3.5
## 불편함을 해소하기 위해 코루틴 등장
## 코루틴 : async def 로 만든 함수 자체를 코루틴이라고 하며 async/await 키워드 사용
## 제너레이터와 마찬가지로 중간에 멈추고 재개할 수 있는 함수임
## async def -> 코루틴 함수 정의 (`@asyncio.coroutine`)
## await -> 이벤트루프에 제어권을 넘김 (`yield from`)
## asyncio.run() -> 이벤트루프 생성 + 코루틴 실행
## gather -> 여러 코루틴 동시 실행
## create_task -> 코루틴 백그라운드 task 로 등록

import asyncio
import time
from datetime import datetime

def ts() -> str:
    return datetime.now().strftime("[%H:%M:%S]")

# 이벤트 루프 모니터링 함수
def print_loop_status(
    checkpoint_name: str
) -> None:
    try:
        current = asyncio.current_task()
        current_name = current.get_name() if current else "없다"

        # 모든 이벤트루프 task
        all_tasks = asyncio.all_tasks()
        task_names = [t.get_name() for t in all_tasks]

        print(f"\n{ts()} 체크포인트 : {checkpoint_name}")
        print(f"{ts()} 현재 제어권을 가진 태스크 : {current_name}")
        print(f"{ts()} 이벤트루프에 있는 모든 태스크 : {task_names}")

    except Exception as e:
        print(f"{ts()} 현재 이벤트루프 실행 중이 아님")


# 비동기 함수
async def fetch(
    name: str,
    delay: float = 2.0
) -> str:
    print_loop_status(f"{name} - fetch 함수 직후 및 await 직전")
    await asyncio.sleep(delay)
    print_loop_status(f"{name} - fetch 함수 await 직후")
    return f"{name} 리턴"

# 케이스 1 : 일반 함수 순차
def run_case1():
    start_time = time.time()
    print(f"{ts()} " + "=" * 30 + "\n케이스 1 : 일반 함수 순차\n", end = "=" * 30 + "\n\n")
    print_loop_status("케이스 1 시작")
    time.sleep(1)
    time.sleep(1)
    print(f"{ts()} 케이스 1 완료 (총 {time.time()-start_time:.2f}초)")

# 케이스 2 : async 순차
async def run_case2():
    start_time = time.time()
    print(f"{ts()} " + "=" * 30 + "\n케이스 2 : async 순차\n", end = "=" * 30 + "\n\n")
    print_loop_status("케이스 2 시작")
    await fetch("async 순차 1", 2)
    await fetch("async 순차 2", 4)
    print(f"\n{ts()} 케이스 2 완료 (총 {time.time()-start_time:.2f}초)")

# 케이스 3 : create_task 
async def run_case3():
    start_time = time.time()
    print(f"{ts()} " + "=" * 30 + "\n케이스 3 : create_task\n", end = "=" * 30 + "\n\n")
    print_loop_status("케이스 3 시작")

    # 이벤트루프에 등록됨
    t1 = asyncio.create_task(fetch("태스크 1", 2))
    t2 = asyncio.create_task(fetch("태스크 2", 4))

    # 아래 print 문은 실행됨
    print_loop_status("케이스 3 - 태스트2개 등록 직후, await 직전")

    print(f"{ts()} await t1 직전")

    # 아래에서 제어권을 이벤트루프에게 넘김 -> 이벤트루프가 대기중인 task 들 실행함
    # 태스크 1 실행 -> fecth 진입 -> sleep 에서 정지
    # 태스크 2 실행 -> fecth 진입 -> sleep 에서 정지
    # 이를 10초라고 가정한다면
    await t1
    print(f"{ts()} await t1 직후") # 여기서는 12초
    await t2
    print(f"{ts()} await t2 직후") # 여기서는 14초 -> 촣 4초

    print(f"\n{ts()} 케이스 3 완료 (총 {time.time()-start_time:.2f}초)")

# 케이스 4 : gather
async def run_case4():
    start_time = time.time()
    print(f"{ts()} " + "=" * 30 + "\n케이스 4 : gather\n", end = "=" * 30 + "\n\n")
    print_loop_status("케이스 4 시작")

    # gather 호출
    # gather 도 넘긴 순서대로 등록/실행 (내부적으로 create_task 함)
    # 여기서 모든 task 가 끝날때 까지 대기함 
    await asyncio.gather(
        fetch("태스트1", 1),
        fetch("태스트2", 2),
        fetch("태스트3", 3)
    )

    print(f"\n{ts()} 케이스 4 완료 (총 {time.time()-start_time:.2f}초)")

# 일반 main
def main():
    run_case1()

# async메인
async def async_main():

    # await run_case2()
    # await run_case3()
    await run_case4()

if __name__ == "__main__":

    # main()

    asyncio.run(async_main())


