# Import 실습 가이드

실행은 항상 실습 폴더 안에서 `uv run -m`으로 한다.
`-m`은 CWD를 `sys.path` 기준으로 삼기 때문에, 실습 폴더 안에서 실행해야 import가 정상 동작한다.

---

## 목표 구조

```
uv_import/
├── main.py
├── utils.py
└── mypackage/
    ├── __init__.py
    ├── math_tools.py
    └── string_tools.py
```

---

## 1. 단일 파일 모듈 import

```python
# utils.py
def greet(name: str) -> str:
    return f"Hello, {name}!"

PI = 3.14159
```

```python
# main.py
import utils
from utils import greet, PI

print(utils.greet("world"))
print(greet("world"))
print(PI)
```

```bash
cd uv_import
uv run -m main
```

---

## 2. 패키지(폴더) 만들기

폴더를 패키지로 인식시키려면 `__init__.py` 가 필요하다.

```python
# mypackage/math_tools.py
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b
```

```python
# mypackage/string_tools.py
def shout(text: str) -> str:
    return text.upper() + "!!!"
```

```python
# mypackage/__init__.py - 공개 API 정리 (비워도 됨)
from mypackage.math_tools import add, multiply
from mypackage.string_tools import shout
```

---

## 3. 패키지 import

```python
# main.py
from mypackage import add, shout          # __init__.py에 노출된 것들
from mypackage.math_tools import multiply  # 서브모듈 직접 지정
from mypackage import string_tools         # 모듈 자체를 import

print(add(1, 2))
print(shout("hello"))
print(multiply(3, 4))
print(string_tools.shout("bye"))
```

---

## 4. 패키지 내부에서 다른 모듈 참조

패키지 내부 파일끼리도 절대 import로 참조한다.

```python
# mypackage/string_tools.py 안에서 math_tools를 쓰고 싶을 때
from mypackage.math_tools import add
```

---

## 실행

```bash
cd uv_import

uv run -m main                # main.py 실행
uv run -m mypackage.math_tools  # 서브모듈 직접 실행
```

---

## 체크리스트

- [ ] `utils.py` 만들어서 import 해보기
- [ ] `mypackage/` 폴더 + `__init__.py` 만들기
- [ ] `__init__.py` 비운 상태로 import 해보기
- [ ] `__init__.py`에 공개 API 정리하고 import 해보기
- [ ] `uv run -m`으로 실행 확인
