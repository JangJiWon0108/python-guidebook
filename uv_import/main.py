from uv_import.service import plus_service

if __name__ == "__main__":
    print("\n" + "="*30 + "\n" + "main 파일의 __name__ if 내부")
    print(f"테스트 : {10} + {20} = {plus_service.get_plus(val1=10, val2=20)}")
    print("main 파일의 __name__ if 끝", end = "\n" + "="*30 + "\n\n")