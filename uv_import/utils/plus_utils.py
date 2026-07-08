def plus_function(
    val1: int,
    val2: int,
) -> int:
    """숫자 2개를 더해서 return"""

    result = val1 + val2

    print(f"plus_function 함수 호출 : {val1} + {val2} = {result}")

    return result

if __name__ == "__main__":
    print("\n" + "="*30 + "\n" + "plus_utils 파일의 __name__ if 내부")
    print(f"plus_function 테스트 : {10} + {20} = {plus_function(val1=10, val2=20)}")
    print("plus_utils 파일의 __name__ if 끝", end = "\n" + "="*30 + "\n\n")