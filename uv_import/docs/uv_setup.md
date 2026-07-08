# uv 기본 세팅

## 설치

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## venv 생성

이 실습은 `python-study/` 루트에 venv 하나를 공유해서 사용한다.

```bash
cd ~/python-study
uv venv --python 3.13
source .venv/bin/activate
```

---

## 프로젝트 초기화

```bash
uv init .
```

생성되는 파일:

```
├── .python-version   # Python 버전 지정
├── pyproject.toml    # 프로젝트 메타데이터 & 의존성
└── main.py
```

`pyproject.toml`의 `name`은 pip 패키지 이름 메타데이터일 뿐, import와는 무관하다.

---

## 패키지 설치

```bash
uv add requests       # 의존성 추가 (pyproject.toml에 자동 기록)
uv add --dev pytest   # 개발용 패키지

uv remove requests    # 제거

uv pip list           # 설치된 패키지 목록
```
