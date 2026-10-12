# 검증·평가 첫걸음

> **통합본 · 2026-10-12** — [01 프로젝트 전체 쉽게 보기](01_프로젝트_전체_쉽게_보기.md)와 [02 검증·평가 파트 상세](02_검증평가_파트_상세.md)를 한 파일로 합친 것입니다. 내용은 같습니다.

> 프로젝트 전체와 4번(검증·평가) 임무를 **주방 이야기**로 설명하는 안내서입니다.
> 같은 내용을 퀴즈·체크리스트가 있는 페이지([검증평가_첫걸음.html](https://skn35shimsungwook.github.io/langchain-migration-helper/docs/guide/검증평가_첫걸음.html))와 인쇄용 [PDF](검증평가_첫걸음.pdf)로도 볼 수 있습니다.

## 이것 세 줄만 기억해도 됩니다

1. AI는 **옛날 주방**만 기억해서, 도구가 이사 간 줄 모르고 옛날 레시피를 줍니다.
2. 우리 프로그램은 **새 주방 안내서를 보고** 레시피를 고친 뒤, **서랍을 직접 열어 보며** 도구가 있는지 확인합니다.
3. 나(4번)는 **요리 대회 심사위원**입니다. 같은 문제 30개로 "우리가 더 잘 고친다"를 숫자로 증명합니다.

---

## 1장. 프로젝트 전체를 주방으로 이해하기

| 코드 세계 | 주방 세계 |
|---|---|
| LangChain | AI 프로그램을 만드는 **주방 도구 세트** |
| 코드 | **레시피** |
| `import` | "어느 **서랍**에서 어떤 **도구**를 꺼내라" |
| 패키지 (`langchain_openai` 등) | **서랍장** 하나 |
| LangChain 1.0 업데이트 | 주방을 **새로 정리**함. 도구가 다른 서랍으로 이사 감 |
| ImportError | "그 서랍에 그런 도구 없어요" |
| ModuleNotFoundError | "그런 서랍 자체가 없어요" |

```python
from langchain.chat_models import ChatOpenAI
# = "langchain 서랍장의 chat_models 칸에서 ChatOpenAI 도구를 꺼내라"
```

| 도구 | 옛날 위치 | 지금 위치 |
|---|---|---|
| ChatOpenAI (AI 모델 연결) | `langchain.chat_models` | `langchain_openai`로 이사 |
| PromptTemplate (질문 틀) | `langchain.prompts` | `langchain_core`로 이사 |
| LLMChain (옛날 조립 방식) | `langchain.chains` | 창고(`langchain_classic`)로 치워짐. 요즘은 `prompt \| llm` |
| initialize_agent (옛날 에이전트) | `langchain.agents` | 없어짐. 요즘은 `create_agent` |

최신 LangChain(1.4.4)에서 옛날 서랍을 열면 실제로 이렇게 됩니다.

```text
from langchain.chat_models import ChatOpenAI
ImportError: cannot import name 'ChatOpenAI'              ← "그 칸에 그런 도구 없어요"

from langchain.chains import LLMChain
ModuleNotFoundError: No module named 'langchain.chains'   ← "그런 칸 자체가 없어요"
```

- **문제**: AI는 인터넷의 옛날 레시피를 많이 보고 배워서, 옛날 서랍 위치를 알려 주고 틀린 줄도 모릅니다. ("버전 지체 환각")
- **해결**: ① 새 주방 안내서(공식 문서)를 보고 고치고(**문서 근거**), ② 서랍을 직접 열어 확인합니다(**실행 근거**). 두 번 확인해서 **"이중 검증"**입니다.

> **헷갈리기 쉬운 점**: 우리 프로그램은 **주방을 정리하지 않습니다.** 새 주방은 LangChain 회사가 이미 정리해 두었습니다. 우리가 고치는 것은 **레시피(사용자의 코드)**입니다. "옛날 서랍 A에서 꺼내라"를 "새 서랍 B에서 꺼내라"로 고쳐 쓰고, B를 열어 보며 도구가 진짜 있는지 확인합니다.

## 2장. 기본 설계: 프로그램은 어떤 순서로 일하나 (앞 → 뒤)

| 순서 | 직원 | 하는 일 (주방 말) | 담당 |
|---|---|---|---|
| ① | analyzer | 레시피를 읽고 "이 도구들, 이사 갔을 수도 있어" 표시 | 3번 |
| ② | retriever | 새 주방 안내서에서 도구의 새 위치 찾기 | 2번 |
| ③ | rewriter | 안내서를 보고 레시피 고쳐 쓰기 | 3번 |
| ④ | **verifier** | **새 주방에서 서랍을 직접 열어 보기** | 1번 |
| ⑤ | report | 고친 레시피 + 안내서 몇 쪽 + 몇 번 만에 성공 | 3번 |

**④에서 도구가 없으면 → 에러 메시지를 들고 ②로 돌아가 다시 찾습니다 (최대 3번).** 이 되돌아가는 길이 **검증 루프**입니다. 일반 AI에는 이 길이 없습니다.

## 3장. 역설계: 발표 장면에서 거꾸로 (뒤 → 앞)

```text
🏆 발표: "같은 문제 30개에서 우리가 일반 AI보다 더 많이 맞혔습니다"
 ↓ 필요한 것
6. 그래프 ............ make_charts.py
 ↓
5. 성적표 ............ run_baseline.py가 만듦 (results/)
 ↓
4. 채점 로봇 .......... verify.py (서랍을 직접 열어 보고 ⭕❌)
 ↓
3. 채점 규칙 .......... EVAL_RULES.md (공정한 시합 규칙표)
 ↓
2. 시험지 30문제 ...... testset.json, 검사기 check_testset.py
 ↓
1. 자료 조사 .......... docs/데이터_출처_조사.md
```

| | 기본 설계 (2장) | 역설계 (3장) |
|---|---|---|
| 방향 | 앞 → 뒤 | 뒤 → 앞 |
| 보는 것 | **프로그램**이 일하는 순서 | **내(4번)**가 일하는 순서 |
| 질문 | "코드를 넣으면 무슨 일이 일어나지?" | "발표에서 보여주려면 뭐가 필요하지?" |

실제로 일하는 순서는 계단을 아래에서 위로(1 → 6) 올라가는 순서입니다. 1~4번은 초안이 완성되어 있습니다.

## 4장. 내 임무: 요리 대회 심사위원

요리사 두 명(일반 AI, 우리 프로그램)에게 **똑같은 옛날 레시피 30개**를 주고 고쳐 오게 합니다. 나는 고쳐 온 레시피대로 **서랍을 실제로 열어 보고**, 도구가 다 있으면 합격을 줍니다.

| 파일 | 주방 비유 | 내가 할 일 |
|---|---|---|
| `EVAL_RULES.md` | 시합 규칙표 | 팀과 빈칸 2개 채우기 (비교 모델, verifier 담당) |
| `testset.json` | 문제지 30장 | 왜 깨지는지 몇 개 설명할 수 있게 하기 |
| `check_testset.py` | 문제지 검사기 | 실행해서 "통과 30/30" 보기 |
| `verify.py` | 채점 로봇 | 1번에게 "우리 시스템도 이걸로 채점해 주세요" 전달 |
| `run_baseline.py` | 상대 선수 시험 기계 | 일반 AI 시험 실행 |
| `make_charts.py` | 점수판 그리기 기계 | 그래프 받기 |

**왜 AI에게 "맞아?"라고 묻지 않나요?** 심사위원도 옛날 주방만 기억하면 틀린 레시피에 합격을 줄 수 있습니다. 그래서 말이 아니라 **서랍을 직접 열어서** 채점합니다.

| 공정한 시합 규칙 | 달리기로 말하면 |
|---|---|
| 같은 AI 두뇌(모델) 사용 | 같은 운동화 |
| 같은 문제 30개, 같은 순서 | 같은 코스 |
| 같은 채점 로봇(`verify.py`) | 같은 시계 |
| 꼼수(어려운 부분 지우기 등)는 실패 | 코스 가로지르면 실격 |

- **꼭 알아야 하는 것**: 왜 서랍을 직접 열어 보는지, 시합이 왜 공정한지, 결과 숫자의 뜻, 한계
- **몰라도 괜찮은 것**: 파이썬 코드 한 줄 한 줄의 뜻 (실행 방법만 알면 됨)
- **한계**: 서랍에서 도구를 **꺼낼 수 있다**고 **올바르게 쓴다**는 보장은 없습니다. 국자를 꺼냈는데 국자로 칼질을 하면 요리는 망합니다.

## 5장. 따라 하기

```powershell
# 0. 평가 폴더로 이동
cd "C:\Users\playdata2\Desktop\skn35 report\langchain_migration\eval"

# 1. 새 주방(검증용 가상환경) 만들기 - 처음 한 번만
uv venv verify-env --python 3.12
uv pip install --python verify-env/Scripts/python.exe langchain langchain-core langchain-openai langchain-community langchain-classic langgraph
verify-env/Scripts/python.exe -m pip freeze > requirements-verify.txt

# 2. 문제지 검사 → "통과: 30 / 30"이 나오면 성공
python check_testset.py testset.json --py verify-env/Scripts/python.exe

# 3. 일반 AI 시험 (내 API 키 넣기, 키는 GitHub에 절대 올리지 않기)
pip install openai matplotlib
$env:OPENAI_API_KEY="sk-...내 키..."
python run_baseline.py --py verify-env/Scripts/python.exe --model [모델명] --limit 3   # 3문제 먼저
python run_baseline.py --py verify-env/Scripts/python.exe --model [모델명]            # 30문제 전체

# 4. 우리 시스템 시험 → 1번 팀원에게 부탁 ("verify.py로 채점, EVAL_RULES 7장 모양으로 저장")

# 5. 점수판 그리기 → charts 폴더에 그래프 3장과 summary.md
python make_charts.py --a results/A_[모델명]_[날짜].json --b results/B_[모델명]_[날짜].json
```

**막히면 Claude에게**: "langchain_migration/eval 폴더에서 *[명령어]*를 실행했더니 이런 에러가 났어. *[에러 전체]* 중학생도 이해하게 원인이랑 해결 방법 알려줘."

## 6장. 결과 읽는 법 (아래 숫자는 연습용 예시)

| 숫자 | 뜻 | 예시 |
|---|---|---|
| 1회차 성공률 | 우리 프로그램이 처음 한 번에 맞힌 비율 | 30개 중 6개 → 20% |
| 최종 성공률 | 다시 찾고 고치기를 최대 3번 해서 맞힌 비율 | 30개 중 27개 → 90% |
| **검증 루프 효과** | 최종 − 1회차 | 90 − 20 = **+70%p** |

**%p**는 퍼센트끼리 뺀 값입니다.

| 성공의 종류 | 주방 비유 |
|---|---|
| 깔끔한 성공 | 새 서랍에서 새 도구를 꺼냄 |
| 성공 (community 경고) | "이번 달까지만 영업" 가게에서 사 온 도구. 곧 못 씀 |
| 성공 (classic 의존) | 창고의 낡은 도구를 꺼내 씀. 요즘 방식은 아님 |
| 실패 | 서랍에 도구가 없음 |

## 7장. 발표 질문 대비

| 질문 | 쉬운 답 |
|---|---|
| import만 확인하면 충분한가요? | 아닙니다. 꺼낼 수 있는지만 확인하고 올바르게 쓰는지는 못 봅니다. 가장 흔한 고장부터 확실히 잡았고, 실제 실행 테스트는 다음 단계입니다. |
| 왜 AI에게 검증을 맡기지 않았나요? | 검증하는 AI도 같은 옛날 지식을 가질 수 있어서입니다. 그래서 실제로 실행해서 확인했습니다. |
| 30개로 충분한가요? | 난이도별 경향을 보려는 목적입니다. 쉬움·중간·어려움을 10개씩 균형 있게 넣었습니다. |
| 문제를 AI로 만들었으면 불공평하지 않나요? | 공식 가이드의 변경 사항을 기준으로 만들었고, 30개 모두 최신 환경에서 깨지는 것을 확인했습니다. 두 선수 모두 같은 문제를 풀었습니다. |
| 일반 AI에 문서를 주면 되지 않나요? | 연구에 따르면 문서를 줘도 실행 성공률이 66% 정도에 머뭅니다. 그래서 실행 확인과 재시도가 필요합니다. |
| 실무 가치는? | 버전 에러를 찾아 고치는 시간을 줄이고, 근거와 검증 결과가 함께 나와 믿을 수 있고, 다른 라이브러리에도 쓸 수 있습니다. |

## 8장. 용어 사전

| 용어 | 쉬운 뜻 |
|---|---|
| 마이그레이션 | 옛날 레시피를 새 주방에 맞게 고치는 일 |
| 버전 지체 환각 | AI가 옛날 주방만 기억해서 틀린 위치를 자신 있게 알려 주는 현상 |
| RAG | AI가 답하기 전에 안내서(문서)를 찾아보게 하는 방법 |
| 가상환경 (verify-env) | 시험용으로 따로 만든 깨끗한 새 주방 |
| 검증 / verifier | 서랍을 직접 열어 보고 도구가 있는지 확인하는 단계 |
| 검증 루프 | 도구가 없으면 안내서를 다시 찾아 고치는 되돌아가는 길 |
| baseline | 비교 기준. 여기서는 일반 AI의 성적 |
| 테스트셋 | 시험 문제지. 옛날 레시피 30개 |
| langchain_classic | 옛날 도구를 모아 둔 창고 |
| langchain_community | "곧 문 닫습니다" 공지가 붙은 가게 |
| JSON | 컴퓨터가 읽기 쉽게 정리한 표 같은 파일 |

## 9장. 확인 퀴즈

<details><summary>Q1. 옛날 코드 <code>from langchain.chat_models import ChatOpenAI</code>를 최신 LangChain에서 실행하면?</summary>에러가 납니다. ChatOpenAI가 <code>langchain_openai</code> 서랍으로 이사 갔기 때문입니다.</details>

<details><summary>Q2. 우리 프로그램이 일반 AI와 다른 두 가지 근거는?</summary>문서 근거(안내서를 보고 고침) + 실행 근거(서랍을 직접 열어 확인)</details>

<details><summary>Q3. verifier에서 도구가 없다고 나오면?</summary>에러 메시지를 들고 retriever로 돌아가 다시 찾습니다. 최대 3번.</details>

<details><summary>Q4. 왜 AI에게 "맞아?"라고 물어서 채점하지 않나요?</summary>채점하는 AI도 옛날 주방만 기억할 수 있기 때문입니다.</details>

<details><summary>Q5. import가 성공하면 코드가 완벽한가요?</summary>아니요. 도구를 꺼낼 수는 있지만 올바르게 쓰는지는 모릅니다.</details>

<details><summary>Q6. baseline은 무슨 뜻인가요?</summary>비교 기준. 여기서는 일반 AI의 성적입니다.</details>

<details><summary>Q7. 1회차 20%, 최종 90%면 검증 루프 효과는?</summary>90 − 20 = +70%p</details>

## 10장. 이번 주 체크리스트

- [ ] 이 안내서를 끝까지 읽고 퀴즈 풀기
- [ ] 팀과 비교 모델 정하기 (EVAL_RULES 9장)
- [ ] 1번에게 verifier 구현과 결과 형식 부탁하기
- [ ] 새 주방(verify-env) 만들고 `requirements-verify.txt` 저장하기
- [ ] `check_testset.py` 실행해서 통과 30/30 보기
- [ ] 쉬움·중간·어려움 문제 하나씩 골라 왜 깨지는지 말로 설명해 보기
- [ ] 일반 AI 시험 3문제 → 30문제 실행하기
- [ ] 우리 시스템 결과 받기
- [ ] `make_charts.py`로 그래프 3장 만들기
- [ ] 발표 자료 `[__]` 칸에 숫자와 그래프 넣기
- [ ] 예상 질문 6개 소리 내어 답해 보기
