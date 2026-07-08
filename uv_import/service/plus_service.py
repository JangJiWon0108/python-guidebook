from uv_import.utils import plus_utils

def get_plus(
    val1: int,
    val2: int
) -> int:
    
    result = plus_utils.plus_function(
        val1 = val1,
        val2 = val2
    )

    print(f"get_plus 함수 호출 : {val1} + {val2} = {result}")

    return result

if __name__ == "__main__":
    print("\n" + "="*30 + "\n" + "plus_service 파일의 __name__ if 내부")
    print(f"get_plus 테스트 : {100} + {200} = {get_plus(val1=10, val2=20)}")
    print("plus_service 파일의 __name__ if 끝", end = "\n" + "="*30 + "\n\n")
