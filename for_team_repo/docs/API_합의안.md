# API 합의안 (1번 ↔ 4번)

> 버전 1.1 · 2026-10-13 · 작성: 4번 (화면 · 평가) · 받는 사람: 1번 (그래프 · 백엔드)
> 상태: **합의 전 (초안)** — 아래 "정할 것"에 답해 주면 확정합니다.
> 1.1 변경: 팀 저장소 코드에 맞춰 **함수 호출을 기본안**으로 바꾸고, **목표 버전(`target_version`)**을 추가했습니다. 아래 0장을 먼저 보세요.
> 함께 보는 문서: [출력모양_합의안.md](출력모양_합의안.md) (응답 본문 = 3번이 만드는 report)

## 0. 팀 저장소 기준으로 바뀐 점 (1.1)

팀 저장소 dev 브랜치를 보니 **FastAPI가 없고, 화면 자리(`app.py`)가 그래프와 같은 저장소 루트에 있습니다.** 그래서 HTTP 서버를 따로 띄우지 않고 **화면이 그래프 함수를 바로 부르는 방식**을 기본안으로 제안합니다. 1번이 만들 것이 함수 하나로 줄어듭니다.

```python
# 1번이 만들 함수 하나 (위치 예: src/graph/supervisor.py)
def run_migration(code: str, target_version: str = "1.x") -> dict:
    """그래프를 한 번 실행하고 report(dict)를 돌려준다. 모양은 출력모양_합의안.md"""
```

| | 기본안: 함수 호출 | 선택: HTTP (아래 1~7장) |
|---|---|---|
| 1번이 만들 것 | `run_migration()` 함수 하나 | 서버 + 주소 3개 |
| 화면 · 평가 설정 | `MIGRATION_FUNC="src.graph.supervisor:run_migration"` | `MIGRATION_API_URL="http://localhost:8000"` |
| 실패 처리 | 검증 실패는 report의 `success: false`, 그래프 오류는 예외 | 검증 실패는 200, 서버 문제만 HTTP 에러 |
| 준비 상태 | 4번 화면 · 평가 코드에 연결 완료 | 4번 화면 · 평가 코드에 연결 완료 (연습용 서버 포함) |

**목표 버전**: 팀 대화에서 "버전을 골라서 돌리면"으로 정했기 때문에, 화면에 **목표 버전 선택**을 넣고 함수와 요청에 `target_version`을 추가했습니다. 지금은 `"1.x"` 하나로 시작하고, 2번 문서가 늘면 값을 추가합니다. report에도 `target_version`이 들어갑니다.

## 한 줄 요약

**주소 3개만 열어 주면 됩니다.** 화면과 평가는 같은 API를 같은 방식으로 부릅니다.

| 주소 | 하는 일 | 누가 부르나 |
|---|---|---|
| `POST /migrate` | 코드 하나를 변환하고 report를 돌려줌 | 화면(한 건씩), 평가(30건을 하나씩 차례로) |
| `GET /info` | 모델, 최대 시도 횟수, 샌드박스 버전 | 화면(연결 상태 배지), 평가(일반 AI와 같은 모델인지 확인) |
| `GET /health` | 살아 있는지 | 확인용 |

```text
화면 (4번) ─┐
            ├─ POST /migrate ─▶ 1번 API ─▶ LangGraph 파이프라인(2·3번) ─▶ report ─▶ 응답
평가 (4번) ─┘
```

**바로 시험해 보기**: [api_stub.py](contracts/api_stub.py)가 이 합의안 그대로 응답하는 연습용 서버입니다. 1번은 응답 모양을 참고하고, 4번은 실제 API가 나오기 전에 이 서버로 화면과 평가를 연결해 두었습니다.

```bash
python docs/contracts/api_stub.py          # http://localhost:8000
```

## 1. POST /migrate

**요청**

```json
{
  "code": "from langchain.chat_models import ChatOpenAI\n...",
  "request_id": "선택. 없으면 서버가 만들어서 응답에 넣음"
}
```

| 필드 | 형식 | 필수 | 규칙 |
|---|---|---|---|
| `code` | 문자열 | ✅ | 비어 있으면 안 됨, 20000자 이하 |
| `target_version` | 문자열 | – | 목표 버전. 지금은 `"1.x"`만 (없으면 `"1.x"`). 지원하지 않는 값이면 400 `unsupported_version` |
| `request_id` | 문자열 | – | 로그를 찾을 때 사용 |

**응답 (200)**: [출력모양_합의안.md](출력모양_합의안.md)의 report에 `request_id`를 더한 것

```json
{
  "contract_version": "1.1",
  "target_version": "1.x",
  "request_id": "b1f0…",
  "original_code": "...",
  "migrated_code": "...",
  "changes": [ ... ],
  "verification": {"success": true, "fail_stage": null, "error": null, "checked_attributes": []},
  "attempts": 2,
  "attempt_log": [ ... ]
}
```

> ⚠️ **검증 실패도 200입니다.** 파이프라인이 끝까지 돌았는데 코드가 검증을 통과하지 못한 것은 "정상적인 결과"입니다. `verification.success: false`로 알려 주세요. HTTP 에러는 **요청 자체를 처리하지 못했을 때만** 씁니다. 그래야 평가에서 "변환 실패"와 "서버 문제"를 구분할 수 있습니다.

## 2. GET /info

```json
{
  "contract_version": "1.0",
  "model": "gpt-4o-mini",
  "max_attempts": 3,
  "sandbox": {"python": "3.12", "langchain": "1.4.4", "langchain-core": "1.6.9"}
}
```

| 필드 | 쓰는 곳 |
|---|---|
| `model` | 평가 실행기가 일반 AI(baseline) 실험과 **같은 모델인지 자동 확인** (EVAL_RULES 5장) |
| `max_attempts` | 화면 배지, 평가 그래프의 시도 횟수 축 |
| `sandbox` | 검증 환경 버전 기록 (평가 결과 보고서에 그대로 적음) |

## 3. GET /health

```json
{"status": "ok"}
```

## 4. 에러 규칙

에러 응답은 모두 같은 모양입니다.

```json
{"error": {"code": "empty_code", "message": "code 에 변환할 코드를 넣어 주세요"}}
```

| HTTP | `code` | 언제 |
|---|---|---|
| 400 | `invalid_json` | 요청 본문이 JSON이 아님 |
| 400 | `empty_code` | `code`가 없거나 비어 있음 |
| 413 | `code_too_long` | `code`가 20000자 초과 |
| 500 | `pipeline_error` | 파이프라인 안에서 예상 못 한 오류 (LLM 호출 실패 등) |
| 504 | `timeout` | 시간 안에 끝나지 않음 |

화면은 이 `message`를 그대로 사용자에게 보여 주고, 평가는 해당 문제를 `fail_stage: "api"`(서버 문제)로 기록합니다.

## 5. 지켜 줄 규칙

1. **응답은 JSON (UTF-8)**, `Content-Type: application/json`.
2. **한 번에 하나씩**: 평가는 30문제를 차례로 하나씩 보냅니다. 동시 요청 처리는 없어도 됩니다.
3. **시간**: 화면과 평가는 응답을 **최대 180초** 기다립니다. 파이프라인이 그보다 오래 걸리면 504보다는, 시도를 멈추고 `fail_stage: "timeout"`인 report를 돌려주는 쪽을 추천합니다.
4. **비밀 정보**: OpenAI API 키 등은 서버 환경 변수에만 두고, 응답이나 로그에 넣지 않습니다.
5. **주소 설정**: 4번 쪽은 환경 변수 `MIGRATION_API_URL`에 기본 주소(예: `http://localhost:8000`)만 넣고, 뒤의 `/migrate`는 코드가 붙입니다.

## 6. 1번이 맞는지 확인하는 방법

```bash
# 살아 있는지
curl http://localhost:8000/health

# 변환 한 건 → 파일로 저장 → 출력 모양 검사 (3번 합의안 기준)
curl -X POST http://localhost:8000/migrate -H "Content-Type: application/json" -d "{\"code\": \"from langchain.chains import LLMChain\"}" -o r.json
python eval/check_contract.py r.json
```

`[PASS]`가 나오면 화면과 평가에 바로 연결됩니다.

## 7. 참고: FastAPI로 만든다면

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

class MigrateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20000)
    request_id: str | None = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/info")
def info():
    return {"contract_version": "1.0", "model": MODEL, "max_attempts": MAX_ATTEMPTS, "sandbox": SANDBOX_VERSIONS}

@app.post("/migrate")
def migrate(req: MigrateRequest):
    state = graph.invoke({"source_code": req.code})      # 1번 LangGraph
    return {**state["report"], "request_id": req.request_id or new_id()}   # report 모양은 3번 합의안
```

FastAPI는 입력 검사 실패를 422로 돌려줍니다. 4장 표처럼 400과 `{"error": …}` 모양으로 맞추려면 에러 처리기를 하나 추가하면 됩니다. 어려우면 422 그대로 두고 알려 주세요. 화면 쪽에서 맞추겠습니다.

## 8. 정할 것 (1번 답변 필요)

| # | 질문 | 4번 제안 |
|---|---|---|
| 1 | 기본 주소와 포트는? | `http://localhost:8000` |
| 2 | 프레임워크는? | FastAPI (7장 참고) |
| 3 | 파이프라인 한 건이 보통 몇 초 걸리나요? 180초면 충분한가요? | 180초, 넘으면 `fail_stage: "timeout"` report |
| 4 | `/info`의 `model`, `max_attempts`, `sandbox` 값을 채울 수 있나요? | 설정 파일이나 환경 변수에서 읽기 |
| 5 | 발표 데모는 노트북 한 대에서 API와 화면을 같이 켜나요? | 예 (같은 노트북, localhost) |

## 9. 1번에게 보낼 메시지

> 1번님, 화면이랑 평가에서 API를 부르는 방식 맞추려고 합의안 만들었어요!
> 주소는 `POST /migrate`, `GET /info`, `GET /health` 세 개만 있으면 되고, `/migrate` 응답은 3번 report 모양 그대로예요.
> 👉 https://github.com/SKN35shimsungwook/langchain-migration-helper/blob/main/docs/API_합의안.md
> 같은 모양으로 응답하는 연습용 서버(`docs/contracts/api_stub.py`)도 있어서 참고하시면 편할 거예요. FastAPI 예시도 7장에 넣어 뒀어요.
> 중요한 것 하나만: **검증 실패도 HTTP 200**으로 주시고(report의 `verification.success: false`), HTTP 에러는 서버 문제일 때만 써 주세요. 평가에서 둘을 구분해야 해서요!
> 8장 "정할 것" 다섯 가지 답 주시면 확정할게요 🙏
