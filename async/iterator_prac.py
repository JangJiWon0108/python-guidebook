import sys

# 리스트에 100만개 올리기
lst = [i for i in range(1000000)]
print(f"리스트에 100만개 올린 후 메모리 : {sys.getsizeof(lst) / 1024 / 1024:.2f}MB")


# 이터레이터 사용
## 이터레이터는 상태(현재 위치)를 기억함. 값을 필요할 때 하나씩 꺼내므로 메모리 사용이 효율적임
## 한 번 소진되면 재사용 불가해서 다시 만들어야 함 
## 이터레이터 프로토콜
## - 이터레이터가 되려면 2가지 메서드가 필요함
## > __iter__() : 이터레이터 객체 자신을 반환
## > __next__() : 다음 값을 반환하며, 더이상 값이 없으면 stop iteration 예외 발생
## 위에서 __ 2개로 감싸진 메서드를 매직 메서드 라고함
## 직접 호출해도 되지만, 관례상 직접 호출하지 않고 파이썬 내장 함수로 호출함
## -> 위 메서드들을 직접 구현하기 번거롭다 - 제너레이터로 해결함

class CountUp:

    # 생성자
    def __init__(self, max):
        self.max = max
        self.current = 0

    # __iter__ 
    def __iter__(self):
        return self

    # __next__
    def __next__(self):

        # 더 이상 반환할 값이 없으면 예외 발생
        # for 루프는 이 예외를 받으면 자동 순회 종료
        if self.current >= self.max:
            raise StopIteration

        # 다음값 반환 
        self.current += 1
        return self.current
        
# ==================== 사용법 1 : iter, next 메서드 사용 ====================

c = iter(CountUp(5))  # c = CountUp(5).__iter__() 와 동일

print(next(c))  # c.__next__() 와 동일
print(next(c))
print(next(c))
print(next(c))
print(next(c))
# print(next(c))  # StopIteration




# ==================== 사용법 2 : for 사용 ====================

# 내부적으로 아래와 같이 동작

# counter = CountUp(5)
# it = iter(counter)

# while True:
#     try:
#         n = next(it)
#         print(n)
#     except StopIteration:
#         break

for i in CountUp(5):
    print(i)
