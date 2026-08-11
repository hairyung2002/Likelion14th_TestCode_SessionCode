# 세션 11 — 테스트 코드

Django + DRF 로 만든 영화 리뷰 API에 테스트 코드를 붙여봅니다.
이 저장소에는 지금까지 세션 1~10을 거쳐 만든 코드가 그대로 들어 있고, **테스트는 아직 한 줄도 없습니다.** 오늘 우리가 직접 작성합니다.

슬라이드가 안 보이는 자리에서도 따라 칠 수 있도록 코드는 전문을 그대로 실었습니다. 타이핑하면서 따라오세요.

---

## 0. 알아두어야 할 것

- `Movie` 에는 좋아요 기능이 없습니다. `click_num` 은 단순 조회수 카운터입니다.
- 인증은 JWT 쿠키 방식입니다(`dj-rest-auth`). 로그인하지 않은 요청은 **401** 이 돌아옵니다. (403이 아닙니다!)
- URL 라우터가 `trailing_slash=False` 로 설정되어 있어 실제 경로는 `/movies` 처럼 끝에 슬래시가 없습니다. 테스트에서 URL을 문자열로 직접 쓰지 말고 `reverse()` 를 사용하세요.

| reverse 이름 | 실제 경로 |
|---|---|
| `movie:movies-list` | `/movies` |
| `movie:movies-detail` | `/movies/1` |
| `movie:comments-detail` | `/comments/1` |
| `movie:movie-comments-list` | `/movies/1/comments` |

---

## 1. 설치, `pytest.ini`, `conftest.py`

### 1-1. 패키지 설치

```bash
pip install -r requirements.txt
```

`pytest`, `pytest-django`, `pytest-cov` 가 이번 세션에서 새로 추가된 패키지입니다.

### 1-2. `pytest.ini`

프로젝트 루트(`manage.py` 와 같은 위치)에 새 파일을 만듭니다.

```ini
[pytest]
DJANGO_SETTINGS_MODULE = project.settings
python_files = test_*.py
```

`pytest-django` 가 이 설정을 보고 어떤 Django 설정 모듈을 쓸지, 어떤 파일을 테스트로 인식할지 판단합니다.

### 1-3. `conftest.py`

역시 프로젝트 루트에 만듭니다. 여러 테스트 파일에서 공통으로 쓰는 픽스처를 모아두는 곳입니다.

```python
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from movie.models import Movie, Comment

User = get_user_model()


@pytest.fixture
def api_client():
    """요청을 보낼 클라이언트."""
    return APIClient()


@pytest.fixture
def user(db):
    """기본 사용자."""
    return User.objects.create_user(username="mentee", password="pw12345!")


@pytest.fixture
def other_user(db):
    """다른 사용자. 남의 것을 건드리는 상황을 만들 때 쓴다."""
    return User.objects.create_user(username="stranger", password="pw12345!")


@pytest.fixture
def movie(db, user):
    """user 가 올린 영화."""
    return Movie.objects.create(writer=user, name="인터스텔라", content="우주 영화 #SF")


@pytest.fixture
def others_movie(db, other_user):
    """other_user 가 올린 영화."""
    return Movie.objects.create(writer=other_user, name="기생충", content="봉준호 #드라마")


@pytest.fixture
def others_comment(db, other_user, movie):
    """other_user 가 쓴 댓글."""
    return Comment.objects.create(movie=movie, writer=other_user, content="재밌어요")
```

픽스처 함수의 인자 이름이 곧 다른 픽스처를 가져다 쓰는 방법입니다. `db` 는 `pytest-django` 가 제공하는 픽스처로, 이게 있어야 테스트 안에서 DB를 사용할 수 있습니다.

`tests/` 디렉터리도 만들고 빈 `tests/__init__.py` 를 넣어둡니다.

```bash
mkdir tests
type nul > tests/__init__.py   # Windows
# touch tests/__init__.py      # macOS/Linux
```

---

## 2. 통합 테스트 — `tests/test_movie_api.py`

API 엔드포인트를 실제로 두드려보는 테스트입니다. `tests/test_movie_api.py` 를 만들고 아래 함수를 하나씩 추가하며 실행해봅니다.

```python
import pytest
from django.urls import reverse

from movie.models import Movie, Comment
```

### A-1 : 로그인하지 않으면 영화를 만들 수 없다

전역 권한 설정이 `IsAuthenticated` 이므로, 인증 없이 보낸 POST는 401이어야 합니다.

```python
@pytest.mark.django_db
def test_create_movie_requires_auth(api_client):
    res = api_client.post(
        reverse("movie:movies-list"),
        {"name": "테스트", "content": "내용"},
    )

    assert res.status_code == 401
```

### A-2 : 남의 댓글은 수정할 수 없다

```python
@pytest.mark.django_db
def test_cannot_update_others_comment(api_client, user, others_comment):
    api_client.force_authenticate(user=user)

    res = api_client.patch(
        reverse("movie:comments-detail", args=[others_comment.id]),
        {"content": "내가 고쳐버림"},
    )

    assert res.status_code == 403
```

`force_authenticate` 는 실제 로그인 절차 없이 요청을 특정 사용자로 인증시켜주는 테스트 전용 기능입니다.

### A-3 : 댓글을 만들면 DB에 실제로 저장된다

응답 상태 코드만 보지 않고, DB에 정말 데이터가 들어갔는지, 그 내용이 맞는지까지 확인합니다.

```python
@pytest.mark.django_db
def test_create_comment_saves_to_db(api_client, user, movie):
    api_client.force_authenticate(user=user)
    before = Comment.objects.count()

    res = api_client.post(
        reverse("movie:movie-comments-list", args=[movie.id]),
        {"content": "좋은 영화네요"},
    )

    assert res.status_code == 201
    assert Comment.objects.count() == before + 1

    created = Comment.objects.latest("id")
    assert created.writer == user
    assert created.movie == movie
```

### 추가 테스트 : 다른 영화의 댓글이 섞여 나오지 않는다

```python
@pytest.mark.django_db
def test_comment_list_is_scoped_to_movie(api_client, user, movie, others_movie):
    Comment.objects.create(movie=movie, writer=user, content="이 영화 댓글")
    Comment.objects.create(movie=others_movie, writer=user, content="다른 영화 댓글")

    api_client.force_authenticate(user=user)
    res = api_client.get(reverse("movie:movie-comments-list", args=[movie.id]))

    assert res.status_code == 200
    assert len(res.data) == 1
    assert res.data[0]["content"] == "이 영화 댓글"
```

### 추가 테스트 : 남의 영화는 삭제할 수 없다

```python
@pytest.mark.django_db
def test_cannot_delete_others_movie(api_client, user, others_movie):
    api_client.force_authenticate(user=user)

    res = api_client.delete(reverse("movie:movies-detail", args=[others_movie.id]))

    assert res.status_code == 403
    assert Movie.objects.filter(id=others_movie.id).exists()
```

여기까지 작성했으면 실행해봅니다.

```bash
pytest -q
```

일부는 통과하고 일부는 실패할 수 있습니다. 실패한다고 테스트 코드가 틀린 게 아닙니다 — **테스트가 실제 버그를 찾아낸 것일 수 있습니다.** 6절에서 다시 다룹니다. 지금은 넘어가도 됩니다.

---

## 3. 레이어 분리 — `services.py`, `selectors.py`

지금 `MovieViewSet` 안에는 태그를 파싱하는 로직(`handle_tags`)이 뷰 메서드로 박혀 있습니다. 이대로면 "태그 파싱 로직만" 테스트하고 싶어도 API를 통째로 호출해야 합니다.

**순수하게 계산만 하는 부분**과 **DB에 접근하는 부분**을 분리하면, 계산 부분은 DB 없이도 빠르게 테스트할 수 있습니다. 이 구분을 위해 두 파일을 만듭니다.

- `movie/services.py` — 무언가를 만들고 바꾸는 동작 (쓰기)
- `movie/selectors.py` — 조회 전용 쿼리 (읽기)

### 3-1. `movie/services.py`

`views.py` 의 `handle_tags` 안에 있던 태그 이름 추출 로직을 순수 함수로 떼어냅니다.

```python
from .models import Tag


def extract_tag_names(content):
    """본문에서 해시태그 이름만 뽑아낸다.

    - '#' 으로 시작하는 단어만 태그로 본다
    - 앞의 '#' 은 떼고, 뒤에 붙은 구두점(.,!?)도 떼어낸다
    - 중복은 제거한다
    """
    words = content.split()

    return {
        word[1:].strip(".,!?")
        for word in words
        if word.startswith("#") and len(word) > 0
    }


def sync_movie_tags(movie):
    """영화 본문을 읽어 태그를 다시 붙인다."""
    movie.tags.clear()

    for name in extract_tag_names(movie.content):
        tag, _ = Tag.objects.get_or_create(name=name)
        movie.tags.add(tag)
```

`extract_tag_names` 는 문자열만 받아서 집합(set)을 돌려주는 순수 함수입니다. DB를 건드리지 않으므로 `@pytest.mark.django_db` 없이도 테스트할 수 있습니다.

### 3-2. `movie/selectors.py`

```python
from .models import Movie, Comment


def get_movie_list():
    """목록 조회용 쿼리셋."""
    return Movie.objects.all()


def get_comments_of_movie(movie_id):
    """특정 영화에 달린 댓글만 가져온다."""
    return Comment.objects.filter(movie_id=movie_id)
```

### 3-3. `views.py` 수정

`movie/views.py` 상단에 두 모듈을 import 합니다.

```python
from . import services, selectors
```

`MovieViewSet.handle_tags` 메서드는 이제 필요 없으니 지우고, 이를 호출하던 곳을 `services.sync_movie_tags(movie)` 로 바꿉니다.

```python
    def perform_create(self, serializer):
        movie = serializer.save(writer=self.request.user)
        services.sync_movie_tags(movie)

    def perform_update(self, serializer):
        movie = serializer.save()
        services.sync_movie_tags(movie)
```

`MovieViewSet` 에 `get_queryset` 을 추가해 목록 조회일 때만 `selectors.get_movie_list()` 를 쓰도록 합니다.

```python
    def get_queryset(self):
        if self.action == "list":
            return selectors.get_movie_list()
        return Movie.objects.all()
```

`MovieCommentViewSet.get_queryset` 도 셀렉터를 쓰도록 바꿉니다.

```python
    def get_queryset(self):
        movie_id = self.kwargs.get("movie_id")
        return selectors.get_comments_of_movie(movie_id)
```

`recommend` 액션은 그대로 둡니다 (`Movie.objects.order_by("?")` 를 직접 사용). 무작위 추천이라 셀렉터로 뺄 이유가 없습니다.

---

## 4. 유닛 테스트 — `tests/test_services.py`, `tests/test_selectors.py`

### B-1 : 가장 단순한 형태

`tests/test_services.py` 를 만듭니다. DB를 쓰지 않으므로 `@pytest.mark.django_db` 가 없습니다.

```python
import pytest

from movie.services import extract_tag_names


def test_extract_single_tag():
    assert extract_tag_names("우주 영화 #SF") == {"SF"}
```

### B-2 : 입력을 여러 개 한 번에 — `parametrize`

케이스마다 함수를 새로 쓰는 대신, `@pytest.mark.parametrize` 로 입력과 기대값 쌍을 나열하면 pytest가 각 쌍을 하나의 테스트처럼 실행하고 결과도 따로 보여줍니다.

```python
@pytest.mark.parametrize(
    "content, expected",
    [
        ("우주 영화 #SF", {"SF"}),               # 기본
        ("#드라마 #코미디", {"드라마", "코미디"}),  # 여러 개
        ("#SF 최고 #SF", {"SF"}),                # 중복 제거
        ("정말 #명작!", {"명작"}),                # 뒤에 붙은 구두점
        ("태그가 없는 문장", set()),               # 태그 없음
        ("# 혼자 있는 샵", set()),                # '#' 만 있는 경우
    ],
)
def test_extract_tag_names(content, expected):
    assert extract_tag_names(content) == expected
```

실행해보고 몇 개가 통과하고 몇 개가 실패하는지 확인하세요.

### B-3 : 셀렉터 테스트 — `tests/test_selectors.py`

셀렉터는 DB를 읽으므로 `@pytest.mark.django_db` 마커가 필요합니다. `get_comments_of_movie` 가 특정 영화의 댓글만 정확히 걸러오는지 확인하는 테스트를 직접 작성해보세요.

조건:
- `movie` 에 댓글 하나, `others_movie` 에 댓글 하나를 만든다
- `get_comments_of_movie(movie.id)` 결과에는 `movie` 의 댓글만 있어야 한다

---

## 5. 쿼리 수 테스트 — `tests/test_query_count.py`

기능은 맞게 동작하는데 쿼리를 너무 많이 날리는 경우가 있습니다. `pytest-django` 가 제공하는 `django_assert_num_queries` 픽스처로 쿼리 횟수를 단언할 수 있습니다.

```python
import pytest
from django.urls import reverse

from movie.models import Movie


@pytest.mark.django_db
def test_movie_list_query_count(api_client, user, django_assert_num_queries):
    for i in range(10):
        Movie.objects.create(name=f"영화{i}", content=f"내용 #태그{i}")

    api_client.force_authenticate(user=user)

    with django_assert_num_queries(3):
        api_client.get(reverse("movie:movies-list"))
```

실행하면 실패하면서 실제로 몇 번의 쿼리가 나갔는지 보여줍니다. `MovieListSerializer` 의 `get_comments_count`, `get_tags` 를 보면, 영화 하나마다 댓글 수 쿼리 한 번 + 태그 조회 쿼리 한 번이 추가로 나갑니다. 영화가 10개면 기본 쿼리 1번 + 20번 = 21번입니다. 이런 걸 **N+1 문제**라고 부릅니다.

이번 세션에서는 이 문제를 테스트로 **찾아내는 것까지만** 합니다. `select_related` / `prefetch_related` 로 고치는 방법은 다음 기회에 다룹니다.

---

## 6. 버그 찾기

지금까지 작성한 테스트를 전부 돌려보면 몇 개는 실패합니다. 실패하는 테스트가 코드의 버그를 가리키고 있는 겁니다. 아래 표를 참고해 원인을 찾고 고쳐보세요. **어디를 고쳐야 하는지는 알려주지 않습니다** — 실패 메시지와 관련 코드를 직접 추적하세요.

| 실패하는 테스트 | 증상 |
|---|---|
| `test_cannot_delete_others_movie` | 남의 영화인데 삭제(204)가 되어버림 |
| `test_cannot_update_others_comment` | 남의 댓글인데 수정(200)이 되어버림 |
| `test_extract_tag_names` 의 `"# 혼자 있는 샵"` 케이스 | `#` 하나만 있는데 빈 문자열이 태그로 인정됨 |
| `test_movie_list_query_count` | 기대한 쿼리 수보다 훨씬 많이 나감 |

힌트:
- 권한 관련 버그 두 개는 `movie/permissions.py` 의 `IswriterOrReadOnly` 를 어디에 연결했는지를 보세요. 이미 만들어져 있는 클래스이니 고칠 필요는 없습니다.
- 태그 버그는 조건문 하나의 부등호를 보세요.
- 쿼리 수 버그는 이번 세션에서는 고치지 않고 원인만 이해하면 충분합니다.

세 개(권한 두 개 + 태그)를 고치고 나면 쿼리 수 테스트 하나만 실패로 남아야 합니다.

---

## 7. CI 연결하기 — `.github/workflows/test.yml`

이 저장소에는 이미 GitHub Actions 워크플로가 들어 있습니다.

```yaml
name: test

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      # 1. 저장소 코드 가져오기
      - uses: actions/checkout@v4

      # 2. 파이썬 설치
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      # 3. 의존성 설치
      - run: pip install -r requirements.txt

      # 4. 테스트 실행
      - run: pytest
```

네 단계가 전부입니다. 코드를 받아오고, 파이썬을 설치하고, 패키지를 깔고, `pytest` 를 실행합니다. DB가 SQLite라서 별도 서비스 컨테이너가 필요 없습니다.

**실습 순서**

1. 이 저장소를 자신의 GitHub 계정으로 올립니다.
2. GitHub 저장소 페이지의 **Actions** 탭을 열어 워크플로가 자동으로 실행되는지 확인합니다.
3. 버그를 고치기 전 커밋과, 고친 후 커밋을 각각 푸시해보고 Actions 결과가 어떻게 바뀌는지 비교합니다.
4. 일부러 테스트를 하나 깨뜨린 커밋을 올려 Actions가 실패로 표시되는 것도 확인해봅니다.
