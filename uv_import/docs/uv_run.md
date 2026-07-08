# uv run 실행 방식 정리

## `uv run 파일명` vs `uv run -m 모듈명`

핵심 차이: **`sys.path`에 뭐가 추가되느냐**

---

## `uv run main.py`

`main.py` **파일이 있는 폴더**가 `sys.path`에 추가됨

```bash
cd python-study
uv run uv-import/main.py
# sys.path → ["uv-import/"]  ← main.py 있는 폴더
```

---

## `uv run -m main`

**CWD(지금 서 있는 폴더)** 가 `sys.path`에 추가됨

```bash
cd python-study
uv run -m uv-import.main
# sys.path → ["python-study/"]  ← CWD
```

---

## 차이가 생기는 경우

```
uv-import/
├── main.py
└── mypackage/
    ├── __init__.py
    └── utils.py
```

```bash
cd python-study   # 루트에서 실행

uv run uv-import/main.py
# sys.path → ["uv-import/"]
# from mypackage import utils  → 동작

uv run -m uv-import.main
# sys.path → ["python-study/"]
# from mypackage import utils  → 에러 (mypackage가 안 보임)
```

---

## 정리

| | `uv run main.py` | `uv run -m main` |
|--|--|--|
| sys.path 기준 | 파일이 있는 폴더 | CWD (내가 서 있는 폴더) |
| 같은 위치에서 실행 시 | 동일 | 동일 |
| 다른 위치에서 실행 시 | 파일 위치 기준 | 실행 위치 기준 |

**파일 지정은 그 파일 위치 기준, `-m`은 내가 서 있는 위치 기준.**

실행 위치와 파일 위치가 같으면 차이 없음.

---

## 실습 권장 방식

```bash
# 각 실습 폴더 안으로 들어가서 실행
cd python-study/uv-import
uv run -m main             # main.py 실행
uv run -m mypackage.utils  # mypackage/utils.py 직접 실행
```

이 방식이면 import도 깔끔하게 쓸 수 있음:

```python
# main.py 안에서
from mypackage import utils
from mypackage.utils import some_func
```
