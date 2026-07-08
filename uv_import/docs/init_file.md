# __init__.py

폴더를 Python 패키지(모듈)로 인식시키기 위한 파일.

---

## 없을 때 vs 있을 때

```
mypackage/
└── utils.py
```

```python
from mypackage import utils  # 에러 - 그냥 폴더라 패키지로 인식 안 됨
```

```
mypackage/
├── __init__.py   ← 추가
└── utils.py
```

```python
from mypackage import utils  # 동작
```

---

## 안에 뭘 써야 하나?

비워도 됨. 존재 자체가 목적.

내용을 쓰면 `import` 시 자동으로 실행됨.

```python
# mypackage/__init__.py
from .utils import add, subtract   # 자주 쓰는 것들을 미리 노출
```

```python
# 쓰는 쪽에서 편해짐
from mypackage import add   # mypackage.utils.add 까지 안 써도 됨
```

---

## 정리

| | |
|--|--|
| 파일 하나 (`.py`) | 그냥 모듈 |
| 폴더 + `__init__.py` | 패키지 (import 가능) |
| `__init__.py` 내용 | 비워도 되고, 공개 API 정리용으로 써도 됨 |
