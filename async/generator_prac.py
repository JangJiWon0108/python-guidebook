# 제너레이터
# 이터레이터를 생성 하려면 __iter__, __next__ 필요함. 
# 이런 과정 필요없이 yield 키워드를 통해 이터레이터를 만드는 것이 제너레이터임
# `yield`
## > 해당 값을 return 후, 함수의 현재 상태를 보존한 채 멈춘다
## > 다음 next 호출 시, 그 다음 (yield) 다음 줄 부터 다시 실행함


def my_gen(max_value: int):
    count = 0
    
    print(f"my_gen 호출 직후 : count = {count}\n")

    for i in range(max_value):
    
        count += 1
        print(f"count 증가 직후 - count : {count}")

        print(f"yield count 직전")
        yield count 
        print(f"yield count 직후")


g = my_gen(3)
print(g)        # 제너레이터 객체 <generator object my_gen at 0x7c015dffd0e0>
print(type(g), end = "\n\n")  # <class 'generator'>

print(f"첫 번재 next 결과 : {next(g)}", end = "\n\n")
print(f"두 번재 next 결과 : {next(g)}", end = "\n\n")
print(f"세 번재 next 결과 : {next(g)}", end = "\n\n")
# print(f"네 번재 next 결과 : {next(g)}", end = "\n\n") # StopIteration