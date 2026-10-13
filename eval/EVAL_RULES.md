# 평가 기준 및 실험 규칙 (EVAL_RULES)

> LangChain 버전 마이그레이션 도우미 챗봇의 성능을 **공정하게 비교**하기 위한 규칙입니다.
> 담당: 4번 (화면 · 평가) · verifier 구현은 3번 (변환 · 검증)
> 이 문서의 규칙은 실험 시작 후 바꾸지 않습니다. 바꿔야 하면 맨 아래 "변경 기록"에 이유와 함께 남깁니다.

---

## 1. 실험 목적

> **일반 LLM보다 우리 시스템(문서 근거 + 실행 검증 루프)이 최신 LangChain에서 실제로 동작하는 코드를 더 많이 만들어 내는가?**

- 비교 대상
  - **A. baseline**: 일반 LLM에 코드만 주고 "최신 버전으로 바꿔줘"라고 요청
  - **B. 우리 시스템**: 오프라인으로 만든 Qdrant · `symbol_map.json`을 근거로 analyzer → retriever → rewriter → verifier → report 파이프라인 실행
  - (선택) **C. langchain-cli migrate**: LangChain 공식 자동 변환 도구

---

## 2. 성공 판정 기준

변환 결과 코드 하나에 대해 아래 순서대로 판정합니다. **1~3을 모두 통과하면 "성공"**입니다.

| 단계 | 검사 | 실패 조건 |
|---|---|---|
| 0 | **코드 추출** | LLM 응답에서 첫 번째 ` ```python ` 코드 블록을 가져옵니다. 없으면 응답 전체를 코드로 봅니다. |
| 1 | **문법 검사** | `ast.parse()`에서 `SyntaxError` 발생 |
| 2-a | **import 실행** | 코드 안의 모든 `import` / `from … import …` 문을 뽑아 검증 환경에서 실행했을 때 에러 발생 (`ImportError`, `ModuleNotFoundError` 등) |
| 2-b | **속성 확인** | import 한 이름에서 바로 이어지는 속성(예: `PromptTemplate.from_template`, `hub.pull`)이 실제로 없음. 없는 기능을 지어낸 코드를 잡습니다. |
| 3 | **무효 변환 검사** | 아래 중 하나에 해당 (사람이 확인) |

**3단계 무효 변환 (꼼수 방지)**
- 코드가 비어 있거나, LangChain import를 전부 지워서 통과한 경우
- 원본에 있던 핵심 구성요소(모델, 프롬프트, 체인/에이전트)가 통째로 사라진 경우

**참고로 기록만 하는 항목 (성공/실패에는 영향 없음)**
- **경고 발생 여부**: import는 되지만 폐기 경고가 나오는 경우 → `warning: true`, 메시지는 `warning_messages`에 기록
  - 확인된 사례: `langchain-community`는 import만 해도 "is being sunset and is no longer actively maintained" DeprecationWarning을 냅니다. (2026-10-12, langchain-community 0.4.2)
- **langchain-community 사용 여부**: `uses_community: true`로 기록. 지금은 통과하지만 앞으로 깨질 수 있는 코드의 비율로 보고합니다.
- **langchain-classic 사용 여부**: `LLMChain` 등을 `langchain_classic`에서 가져와 통과한 경우 → `uses_classic: true`로 기록
  - 공식적으로 허용된 방법이므로 성공으로 인정합니다.
  - 다만 "최신 방식으로 바꾼 것"과는 다르므로 결과 보고 때 비율을 따로 표시합니다.

> ⚠️ **한계**: 판정은 "부품을 가져올 수 있고, 그 부품의 기능 이름이 실제로 있다"까지입니다.
> 함수 인자가 틀리거나, 변수에 담은 뒤 쓰는 기능(`llm.invoke` 등), 실행 결과가 맞는지는 잡지 못합니다. 결과 보고와 발표에서 반드시 이 한계를 명시합니다.
>
> 2-a, 2-b는 3번이 만드는 verifier (b) "샌드박스 import · 속성 검증"과 **같은 기준**입니다. `eval/verify.py`를 verifier의 출발점으로 넘겨 판정 기준을 하나로 맞춥니다.

---

## 3. 평가 지표

| 지표 | 계산 방법 | 보여주려는 것 |
|---|---|---|
| **전체 성공률** | 성공 개수 ÷ 전체 개수 × 100 | 핵심 성과 (A vs B) |
| **난이도별 성공률** | 난이도별 성공 개수 ÷ 난이도별 개수 × 100 | 어려운 코드일수록 차이가 커지는가 |
| **1회차 성공률** | B에서 첫 시도에 성공한 개수 ÷ 전체 × 100 | 검증 루프 없이도 얼마나 되는가 |
| **최종 성공률** | B에서 최대 재시도 안에 성공한 개수 ÷ 전체 × 100 | |
| **검증 루프 효과** | 최종 성공률 − 1회차 성공률 | **실행 검증 루프가 실제로 도움이 되었는가** |
| **평균 시도 횟수** | 성공한 항목들의 시도 횟수 평균 | 비용 대비 효과 |
| **경고 비율** | `warning: true` 개수 ÷ 성공 개수 | 통과했지만 곧 깨질 코드의 비율 |
| **classic 의존 비율** | `uses_classic: true` 개수 ÷ 성공 개수 | 진짜 최신 방식으로 바꾼 비율 |
| **근거 일치율** (B만) | 근거 ID가 실제 검색 결과에 있던 변경 수 ÷ 전체 변경 수 (verifier (a) 결과) | "문서 근거"가 지어낸 것이 아님을 숫자로 보여 줌 |
| **실패 원인 분포** | 실패한 항목의 `fail_stage` · 에러 종류별 개수 | 어디서 막히는지 (경로 오류, 없는 기능 등) |

---

## 4. 테스트셋 기준

### 4-1. 구성

| 난이도 | 개수 | 정의 | 예시 유형 |
|---|---|---|---|
| **쉬움 (easy)** | 10 | import 경로만 바뀐 코드 | `langchain.chat_models` → `langchain_openai` |
| **중간 (medium)** | 10 | 체인 구조를 바꿔야 하는 코드 | `LLMChain`, `SequentialChain`, `ConversationChain` → LCEL (`prompt \| llm`) |
| **어려움 (hard)** | 10 | 에이전트·메모리 구조를 바꿔야 하는 코드 | `initialize_agent`, `AgentExecutor`, `ConversationBufferMemory` → `create_agent` 등 |

### 4-2. 포함 조건
- [ ] **최신 검증 환경에서 실패**해야 합니다. (처음부터 성공하는 코드는 테스트 의미가 없음)
- [ ] 10~30줄 길이
- [ ] **실제 API 호출 없이** 판정 가능해야 합니다. (API 키 불필요)
- [ ] 깨지는 이유를 한 줄로 설명할 수 있어야 합니다. (`why_broken`)
- [ ] (선택) 구버전 환경에서는 import가 성공하는지 확인 → `verified_old: true`

### 4-3. 저장 형식 (`eval/testset.json`)

```json
[
  {
    "id": "easy_01",
    "difficulty": "easy",
    "old_code": "from langchain.chat_models import ChatOpenAI\nllm = ChatOpenAI()",
    "why_broken": "OpenAI 연동이 langchain-openai 패키지로 분리됨",
    "target_imports": "from langchain_openai import ChatOpenAI",
    "reference": "LangChain v1 migration guide",
    "verified_new_fails": true,
    "verified_old": false
  }
]
```

---

## 5. 실험 조건 (A, B 동일하게 고정)

| 항목 | 규칙 | 값 |
|---|---|---|
| **LLM 모델** | A와 B는 **같은 모델** 사용 | `______` (팀 확정 후 기입) |
| **temperature** | 결과 재현을 위해 고정 | `0` |
| **실행 횟수** | 항목당 1회 실행 (시간이 남으면 3회 실행 후 평균) | `1` |
| **입력** | 같은 `testset.json` 30개를 같은 순서로 사용 | |
| **최대 시도 횟수 (B)** | 첫 시도 포함. 팀 설계는 2~3회이며 실험에서는 한도를 하나로 고정 | `3` (팀이 2회로 정하면 `2`로 바꾸고 `make_charts.py --max-attempts 2`) |
| **판정 도구** | A, B 모두 **같은 verifier**로 판정 | |

### 5-1. baseline(A) 프롬프트 (문구 고정, 수정 금지)

```text
다음 Python 코드는 구버전 LangChain으로 작성되었습니다.
LangChain 1.x 최신 버전에서 동작하도록 코드를 변환해 주세요.
변환된 전체 코드를 ```python 코드 블록 하나로 출력해 주세요.

{old_code}
```

- 일반 사용자가 ChatGPT에 물어보는 상황을 재현하기 위해 **문서나 힌트는 주지 않습니다.**
- B의 프롬프트를 고칠 때 A의 프롬프트는 건드리지 않습니다.

---

## 6. 검증 환경

| 항목 | 규칙 |
|---|---|
| **환경 분리** | 개발용 환경과 별도의 가상환경(`verify-env`)을 만듭니다. |
| **설치 패키지** | `langchain`, `langchain-core`, `langchain-openai`, `langchain-community`, `langchain-classic`, `langgraph` |
| **버전 고정** | 실험 첫날 최신 버전을 설치한 뒤 `pip freeze > eval/requirements-verify.txt`로 고정합니다. 이후 실험 끝날 때까지 업그레이드 금지. |
| **실행 방식** | 코드에서 import 문만 뽑아 `subprocess`로 실행하고, import 한 이름의 속성이 있는지 확인합니다. 생성된 코드 전체는 실행하지 않습니다. (API 호출 등 부작용 방지) |
| **타임아웃** | 항목당 `30초`. 초과하면 실패로 처리합니다. |
| **경고 기록** | `-W always`로 실행해 경고 메시지를 수집합니다. |

> 참고 기준 버전: `langchain 1.4.4` (2026-10-12 PyPI 기준 최신). 실제 값은 `requirements-verify.txt`를 따릅니다.

---

## 7. 결과 기록 형식

실행 결과는 `eval/results/{A|B|C}_{날짜}.json`에 항목별로 저장합니다.

```json
{
  "id": "medium_03",
  "system": "B",
  "success": true,
  "attempts": 2,
  "first_try_success": false,
  "fail_stage": null,
  "error": null,
  "checked_attributes": ["PromptTemplate.from_template"],
  "warning": false,
  "uses_classic": false,
  "invalid_transform": false,
  "evidence": {"total": 3, "valid": 3},
  "attempt_log": [
    {"attempt": 1, "fail_stage": "import", "error_type": "ModuleNotFoundError", "target": "langchain.chains"},
    {"attempt": 2, "fail_stage": null}
  ],
  "migrated_code": "..."
}
```

- `fail_stage`: 실패한 단계 (`syntax` / `import` / `attribute` / `invalid` / `timeout`)
- `error`: 마지막 에러 메시지 한 줄
- `checked_attributes`: 2-b에서 확인한 속성 목록
- `evidence` (B만): verifier (a) 결과. 변경 목록의 근거 ID 중 실제 검색 결과에 있던 개수
- `attempt_log` (B만): 시도별 실패 단계, 에러 종류, 대상 심볼. verifier가 retriever에 돌려보낸 피드백과 같은 내용입니다. (재검색이 무엇을 고쳤는지 발표 자료로 활용)
- A(baseline)는 1회만 시도하므로 `attempts: 1`, `evidence`와 `attempt_log`는 없습니다.

---

## 8. 결과 보고 방법

1. **요약표**: A / B / (C)의 전체 성공률, 난이도별 성공률
2. **그래프**
   - 막대그래프: 시스템별 × 난이도별 성공률
   - 누적 그래프: B의 시도 횟수(1→2→3회)에 따른 누적 성공률
3. **실패 사례 분석**: A와 B에서 각각 대표 실패 사례 3개씩, 원인 분류
   - 원인 분류: `경로 오류`(import) / `없는 기능 생성`(attribute) / `구버전 방식 유지` / `무효 변환` / `기타`
4. **한계 명시**: 2장의 "한계"를 그대로 포함

---

## 9. 팀 확정 체크리스트

실험 시작 전에 팀과 합의하고 체크합니다.

- [ ] 비교에 쓸 LLM 모델: `______`
- [ ] 최대 시도 횟수: 팀 설계 2~3회 중 하나로 확정 (기본 3)
- [ ] 3번과 B 결과 형식 합의: `attempts`, `first_try_success`, `evidence`, `attempt_log` (7장)
- [ ] 2번의 `symbol_map.json`과 `testset.json`의 `target_imports`가 서로 맞는지 대조
- [x] verifier 구현 담당: 3번 (변환 · 검증). `verify.py` 판정 기준을 그대로 쓰기로 합의할 것
- [ ] `requirements-verify.txt` 버전 고정 완료
- [ ] `testset.json` 30개 완성 및 팀 공유
- [ ] C(langchain-cli) 비교군 포함 여부: 포함 / 제외

---

## 10. 변경 기록

| 날짜 | 변경 내용 | 이유 |
|---|---|---|
| 2026-10-12 | 최초 작성 | |
| 2026-10-12 | 결과 기록에 `warning_messages`, `uses_community` 추가 | langchain-community가 import 시 지원 종료 경고를 내는 것을 확인함 |
| 2026-10-12 | 테스트셋 형식에 `target_imports`(정답 방향 import, 최신 환경 통과 확인) 추가 | 정답 방향이 실제로 존재하는지 확인하고, 발표 때 근거로 쓰기 위해 |
| 2026-10-12 | 판정 2-b(속성 확인) 추가, 근거 일치율 · 실패 원인 분포 지표 추가, B 결과에 `evidence` · `attempt_log` 추가, 최대 시도 2~3회 반영 | 팀 설계가 바뀜: verifier가 (a) 근거 ID 확인 (b) 샌드박스 import · 속성 검증을 하므로 평가 기준을 같게 맞춤. 역할도 4번 = 화면 · 평가, verifier = 3번으로 확정 |
