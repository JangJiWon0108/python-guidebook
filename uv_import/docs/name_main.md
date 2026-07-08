# if __name__ == "__main__"

파이썬 파일이 직접 실행될 때만 코드를 실행하는 조건.

---

## __name__ 이란?

파이썬은 파일 실행 시 `__name__` 변수를 자동으로 설정한다.

| 상황 | `__name__` 값 |
|--|--|
| 직접 실행 (`python utils.py`) | `"__main__"` |
| 다른 파일에서 import | 파일 이름 (`"utils"`) |

---

## 예시

```python
# utils.py
def add(a, b):
    return a + b

print("utils 실행됨")        # import 해도 무조건 실행됨

if __name__ == "__main__":
    print("직접 실행할 때만") # import 하면 실행 안 됨
    print(add(1, 2))
```

```python
# main.py
import utils  # → "utils 실행됨" 만 출력
              # → "직접 실행할 때만" 은 출력 안 됨
```

```bash
python utils.py  # → 둘 다 출력
```

---

## 왜 쓰냐?

모듈로 import 될 때는 함수 정의만 로드되고, 테스트/실행 코드는 돌아가지 않게 막기 위해서.

```python
# utils.py
def add(a, b):
    return a + b

if __name__ == "__main__":
    print(add(1, 2))  # 직접 실행할 때만 동작, import 시엔 무시됨
```
