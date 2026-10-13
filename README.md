# LangChain 버전 마이그레이션 도우미

> 구버전 LangChain 코드를 최신 버전(1.x)으로 바꿔 주고, **바꾼 코드가 실제로 동작하는지까지 확인하는** 코드 마이그레이션 챗봇

**문서 근거**(공식 마이그레이션 가이드 · 릴리스 노트 검색)와 **실행 근거**(최신 환경에서 import · 속성 검증)로 이중 검증합니다.
검증에 실패하면 에러 종류와 대상을 피드백으로 다시 검색해서 고칩니다.

**바로 가기**: [발표 자료](https://skn35shimsungwook.github.io/langchain-migration-helper/presentation/발표자료.html) · [쉬운 안내서](docs/guide_v2/01_프로젝트_한눈에.md) · [역할 분담표](docs/역할분담표.md) · [평가 규칙](eval/EVAL_RULES.md) · [안내서 모음 웹페이지](https://skn35shimsungwook.github.io/langchain-migration-helper/)

| | |
|---|---|
| 과제 주제 | LLM을 연동한 내외부 문서 기반 질의응답 시스템 |
| 팀 | [팀 이름] (SKN35) |
| 기간 | [시작일] ~ [발표일] |

## 진행 상황 (2026-10-13 기준)

| 구분 | 내용 | 상태 |
|---|---|---|
| 역할 분담 | 1 그래프·백엔드 / 2 데이터·검색 / 3 변환·검증 / 4 화면·평가 ([역할분담표](docs/역할분담표.md)) | ✅ 확정 |
| 평가 설계 | 평가 기준과 실험 규칙 ([EVAL_RULES.md](eval/EVAL_RULES.md)), 팀 verifier와 같은 판정 기준 | ✅ 완료 |
| 테스트셋 | 구버전 코드 30개, 최신 환경에서 깨지는 것 확인 ([testset.json](eval/testset.json)) | ✅ 완료 |
| 평가 도구 | 판정기(import · 속성), baseline 실험, 그래프 스크립트 | ✅ 완료 (API 없이 흐름 확인) |
| 화면 | 변환하기 탭, 성능 비교 탭 ([app/](app/)) | 🟡 뼈대 완성 (가짜 응답으로 동작) |
| 안내서 v2 | 프로젝트 한눈에 / 화면·평가 파트 (MD · PDF · 웹) | ✅ 완료 |
| 발표 자료 | 14장 초안 (그림 중심) | 🟡 초안 (결과 숫자 미입력) |
| 챗봇 본체 | 오프라인 준비, 파이프라인, 검색, 변환·검증 (1~3번) | ⏳ 진행 중 |
| 실험 | 일반 AI vs 우리 시스템 30문제 비교 | ⏳ 챗봇 완성 후 |

---

## 1. 문제: 버전 지체 환각

![LangChain 1.0에서 도구가 새 서랍으로 이사 간 모습](docs/images/01_kitchen_move.svg)

LangChain은 1.0에서 패키지가 나뉘고, 옛 체인과 에이전트(`LLMChain`, `initialize_agent` 등)가 빠졌습니다.
그런데 인터넷에 쌓인 코드는 대부분 구버전이라, LLM은 복잡한 질문일수록 구버전 코드를 답합니다.

```text
# LangChain 1.4.4에서 실행한 결과
from langchain.chat_models import ChatOpenAI   → ImportError: cannot import name 'ChatOpenAI'
from langchain.chains import LLMChain          → ModuleNotFoundError: No module named 'langchain.chains'
```

더 큰 문제는 **LLM이 자기 답이 틀렸다는 것을 모른다**는 점입니다.
연구에서도 문서가 부족하면 LLM 코드의 42.55%만, 구조화된 문서를 줘도 66.36%만 목표 환경에서 실행된다고 보고합니다. ([When LLMs Lag Behind, 2026](https://arxiv.org/abs/2604.09515))

## 2. 해결: 이중 검증

![같은 옛날 레시피, 두 요리사](docs/images/02_two_cooks.svg)

| 구분 | 일반 LLM | 우리 시스템 |
|---|---|---|
| 근거 | 학습 데이터 (구버전이 다수) | 공식 가이드 · 릴리스 노트 (Qdrant, symbol_map) |
| 확인 | 없음 | 근거 ID 확인 + 샌드박스 import · 속성 검증 |
| 틀렸을 때 | 모름 | 에러 종류 · 대상을 피드백으로 재검색 후 재작성 (최대 2~3회) |
| 답변 | 코드만 | 코드 + 변경표(구 → 신, 근거 링크, 검증 결과) + 시도 횟수 |

## 3. 시스템 구조

![새 설계 한눈에 보기](docs/images/08_system_v2.svg)

**오프라인 (한 번, 2번)**: 마이그레이션 가이드 · 릴리스 노트 수집 → 섹션 · before/after 코드 단위 청킹 → 임베딩 → Qdrant 저장, `symbol_map.json`(구 심볼 → 신 심볼, 근거 ID) 생성

**온라인 (요청마다)**

| 단계 | 하는 일 | 담당 |
|---|---|---|
| ① analyzer | ast로 import · 클래스 · 함수 심볼 추출 | 3번 |
| ② retriever | `symbol_map` 정확 조회 + Qdrant 검색 (에러 피드백 반영) | 2번 |
| ③ rewriter | LLM이 {새 코드, 변경 목록(근거 ID 포함)} 구조화 출력 | 3번 |
| ④ verifier | (a) 근거 ID가 실제 검색 결과에 있는지 (b) 샌드박스에서 import · 속성 검증. 실패하면 에러 종류 · 대상을 피드백으로 ②로 (최대 2~3회) | 3번 |
| ⑤ report | 변환 코드 + 변경표(구 → 신, 근거 링크, 검증 결과) + 시도 횟수 | 3번 |

단계 연결, 다시 갈지 판단, API는 1번이 맡습니다. **화면과 평가는 파이프라인 바깥**에서 API로 파이프라인을 불러 쓰며, 4번이 맡습니다.

- 파이프라인: LangGraph · LLM: [모델명] · 벡터 DB: Qdrant · 화면: Streamlit
- 근거 자료: [LangChain v1 마이그레이션 가이드](https://docs.langchain.com/oss/python/migrate/langchain-v1), 릴리스 노트

## 4. 평가 방법

![요리 대회 심사위원](docs/images/05_judge_contest.svg)

같은 테스트 코드 30개를 **일반 LLM(baseline)**과 **우리 시스템**에 넣고, 같은 판정기로 성공률을 비교합니다. 자세한 규칙은 [eval/EVAL_RULES.md](eval/EVAL_RULES.md)에 있습니다.

| 난이도 | 개수 | 유형 |
|---|---|---|
| 쉬움 | 10 | import 경로만 바뀜 (chat_models, prompts, loaders 등) |
| 중간 | 10 | 체인 구조 변경 (LLMChain, RetrievalQA, 라우터 체인 등) |
| 어려움 | 10 | 에이전트 · 메모리 변경 (initialize_agent, AgentExecutor 등) |

- **성공 기준**: 문법 통과 + import 성공 + **import 한 이름의 속성이 실제로 있음** + 무효 변환 아님
- **판정 기준 통일**: 평가 판정기 `eval/verify.py`를 팀 verifier (b)의 출발점으로 넘겨, 파이프라인 검증과 평가 채점이 같은 기준을 씁니다.
- **공정성**: 같은 모델, temperature 0, 같은 입력, 같은 판정기
- **지표**: 전체 · 난이도별 성공률, 1회차 · 최종 성공률, 검증 루프 효과, 근거 일치율, 실패 원인 분포, 성공의 질(community 경고, classic 의존)

## 5. 결과

> ⏳ 실험 전입니다. 실험 후 `make_charts.py`가 만든 `eval/charts/summary.md`와 그래프 3장으로 이 부분을 채웁니다. 화면의 [성능 비교] 탭에도 같은 결과가 나타납니다.

| 시스템 | 전체 | 쉬움 | 중간 | 어려움 |
|---|---|---|---|---|
| 우리 시스템 | [__]% | [__]% | [__]% | [__]% |
| 일반 LLM (baseline) | [__]% | [__]% | [__]% | [__]% |

- 우리 시스템 1회차 성공률: [__]% → 최종 성공률: [__]%
- **검증 루프 효과: +[__]%p** · 근거 일치율: [__]%

## 6. 실험 중 발견한 것

![성공의 질 네 가지](docs/images/07_success_quality.svg)

- **`langchain-community`는 import만 해도 지원 종료 경고를 냅니다.** (2026-10-12, langchain-community 0.4.2) 지금은 통과해도 곧 깨질 수 있어 `uses_community`로 따로 집계합니다.
- **`langchain_classic`으로 우회하면 옛 체인도 import가 됩니다.** 최신 방식은 아니므로 `uses_classic`으로 따로 집계합니다.
- `langchain_classic.agents`의 `initialize_agent`, `load_tools`는 의존성 문제로 import에 실패했습니다. 어려움 문제는 우회도 잘 되지 않습니다.

## 7. 한계와 다음 단계

| 한계 | 다음 단계 |
|---|---|
| 속성 이름까지는 확인하지만, 함수 인자나 실행 결과는 확인하지 못함 | 가짜 LLM으로 코드 전체 실행 테스트 추가 |
| 테스트 30개를 팀이 직접 구축 | 공개 저장소의 실사용 코드로 확장 |
| 구버전 환경에서 동작하는지는 확인하지 않음 | 구버전 환경을 따로 만들어 교차 확인 |
| LangChain만 대상 | pydantic, OpenAI SDK 등 다른 라이브러리로 확장 |

## 8. 실행 방법

### 8-1. 화면 (4번)

```bash
pip install -r app/requirements.txt
streamlit run app/streamlit_app.py
```

백엔드가 연결되기 전에는 테스트셋 예제로 만든 **가짜 응답**으로 동작합니다. 1번의 API 주소를 환경 변수 `MIGRATION_API_URL`에 넣으면 실제 파이프라인을 부릅니다. report 출력 모양은 [`app/backend.py`](app/backend.py) 맨 위에 있습니다.

### 8-2. 챗봇 본체

```bash
[1번 팀원 확인 후 작성: 오프라인 준비와 API 실행 명령]
```

### 8-3. 평가 재현

`eval` 폴더에서 실행합니다. 쉬운 설명은 [02 화면·평가 파트](docs/guide_v2/02_화면평가_파트.md) 4장에 있습니다.

```bash
uv venv verify-env --python 3.12
uv pip install --python verify-env/Scripts/python.exe langchain langchain-core langchain-openai langchain-community langchain-classic langgraph
verify-env/Scripts/python.exe -m pip freeze > requirements-verify.txt
python check_testset.py testset.json --py verify-env/Scripts/python.exe
python run_baseline.py --py verify-env/Scripts/python.exe --model [모델명]
python make_charts.py --a results/A_[모델명]_[날짜].json --b results/B_[모델명]_[날짜].json
```

OpenAI API 키는 환경 변수 `OPENAI_API_KEY`로 설정합니다. `run_baseline.py`는 `--limit 3`(3문제 먼저), `--mock`(API 없이 흐름만 확인)을 지원합니다.

## 9. 폴더 구조

```text
langchain_migration/
├── README.md
├── index.html                 # GitHub Pages 목차 페이지
├── [graph/ data/]             # 오프라인 준비, 파이프라인 (1~3번, 예정)
├── app/                       # 화면 (4번)
│   ├── streamlit_app.py       # 변환하기 · 성능 비교 탭
│   └── backend.py             # API 호출 / 가짜 응답, report 출력 모양
├── eval/                      # 평가 (4번)
│   ├── EVAL_RULES.md          # 평가 기준과 실험 규칙
│   ├── testset.json           # 테스트 코드 30개
│   ├── check_testset.py       # 테스트 코드가 최신 환경에서 깨지는지 확인
│   ├── verify.py              # 공용 판정기 (import · 속성), 팀 verifier (b)의 출발점
│   ├── run_baseline.py        # baseline(일반 LLM) 실험
│   └── make_charts.py         # 결과 그래프와 요약표
├── presentation/              # 발표 자료 (원본, 웹 버전, PDF)
└── docs/
    ├── guide_v2/              # 쉬운 안내서 최신 (MD · PDF · HTML)
    ├── images/                # 설명 그림 (움직이는 SVG, static/은 슬라이드용 정지 그림)
    ├── 역할분담표.md
    ├── 작업기록.md
    ├── 데이터_출처_조사.md
    ├── guide/                 # 안내서 이전 버전 v1
    └── 역순설계_쉽게_이해하기.md  # 이전 버전 (초판)
```

## 10. 문서 모음

| 문서 | 내용 | 보기 |
|---|---|---|
| **발표 자료** (초안) | 14장, 웹에서는 그림이 움직이고 발표자 노트 포함 | [웹](https://skn35shimsungwook.github.io/langchain-migration-helper/presentation/발표자료.html) · [PDF](presentation/발표자료.pdf) |
| **01 프로젝트 한눈에** (최신 v2) | 주방 비유, 새 설계(기본 설계), 역할, 용어 사전 (팀 모두용) | [MD](docs/guide_v2/01_프로젝트_한눈에.md) · [PDF](docs/guide_v2/01_프로젝트_한눈에.pdf) · [웹](https://skn35shimsungwook.github.io/langchain-migration-helper/docs/guide_v2/01_프로젝트_한눈에.html) |
| **02 화면·평가 파트** (최신 v2) | 역설계, 평가, 화면, 따라 하기, 결과 읽기, 맞출 것, 발표 질문, 체크리스트 | [MD](docs/guide_v2/02_화면평가_파트.md) · [PDF](docs/guide_v2/02_화면평가_파트.pdf) · [웹](https://skn35shimsungwook.github.io/langchain-migration-helper/docs/guide_v2/02_화면평가_파트.html) |
| **역할 분담표** | 네 역할, 1번과 3번의 경계, 서로 맞춰야 하는 것 | [MD](docs/역할분담표.md) |
| 평가 기준과 실험 규칙 | 성공 기준, 지표, 실험 조건, 결과 형식 | [MD](eval/EVAL_RULES.md) |
| 작업 기록 | 무엇을 왜 했는지, 확인한 결과와 남은 일 | [MD](docs/작업기록.md) |
| 데이터 출처 조사 | RAG 문서와 테스트 코드 출처 | [MD](docs/데이터_출처_조사.md) |
| 이전 버전 | 안내서 v1(역할 변경 전), 역순 설계 초판 | [guide/](docs/guide/) · [역순설계](docs/역순설계_쉽게_이해하기.md) |

## 11. 팀

| 역할 | 담당 | 이름 |
|---|---|---|
| 1번 | 그래프 · 백엔드 (State, LangGraph 연결, 재시도 조건, API, 샌드박스 환경) | [이름] |
| 2번 | 데이터 · 검색 (문서 수집, 청킹, Qdrant, symbol_map, retriever) | [이름] |
| 3번 | 변환 · 검증 (analyzer, rewriter, verifier, report) | [이름] |
| 4번 | 화면 · 평가 (Streamlit 화면, 실험 설계, 테스트셋, 비교 실험) + 보고서, README, 발표 | [이름] |

## 12. 참고 자료

- [LangChain v1 마이그레이션 가이드](https://docs.langchain.com/oss/python/migrate/langchain-v1)
- [LangChain 공식 문서 llms-full.txt](https://docs.langchain.com/llms-full.txt)
- Ashik et al., [When LLMs Lag Behind: Knowledge Conflicts from Evolving APIs in Code Generation](https://arxiv.org/abs/2604.09515), 2026
- [GitChameleon 2.0: Evaluating AI Code Generation Against Python Library Version Incompatibilities](https://arxiv.org/abs/2507.12367), 2025
- Wu et al., [VersiCode: Towards Version-controllable Code Generation](https://arxiv.org/abs/2406.07411), 2024
