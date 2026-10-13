# symbol_map · 근거 ID 합의안 (2번 ↔ 3번 · 4번)

> 버전 1.1 · 2026-10-13 · 작성: 4번 (화면 · 평가) · 받는 사람: 2번 (데이터 · 검색), 참고: 1번 · 3번
> 상태: **합의 전 (초안)** — 아래 "정할 것"에 답해 주면 확정합니다.
> 1.1 변경: 팀 저장소의 `MigrateState`(1번이 만든 모양)와 필드를 어떻게 이어 붙이는지 0장에 추가했습니다. symbol_map 파일 모양은 그대로입니다.
> 함께 보는 문서: [출력모양_합의안.md](출력모양_합의안.md) (report의 `evidence_id`, `evidence_url`), [API_합의안.md](API_합의안.md)

## 0. 팀 코드의 `MigrateState`와 연결 (1.1)

팀 저장소 `src/graph/state.py`에는 1번이 만든 모양이 있습니다.

```python
class MigrateState(BaseModel):
    old: str
    new: str
    evidence_id: str
    kind: Literal["native", "classic_fallback"]
```

이것은 **"이번 변환에서 고른 이사 한 건"**이고, symbol_map 한 줄은 **"고를 수 있는 이사 방법 전부"**입니다. 그래서 이름을 바꾸지 않고 아래처럼 이어 붙이면 됩니다.

| `MigrateState` | symbol_map 한 줄에서 가져오는 값 | report `changes[]` |
|---|---|---|
| `old` | `old` | `old` (코드 줄) |
| `new` | 최신 방식이면 `new_import` (없어진 것이면 `replacement_imports`), classic 우회면 `fallback_import` | `new` |
| `evidence_id` | `evidence_ids` 중 실제로 쓴 것 하나 | `evidence_id` |
| `kind` | `new_import` · `replacement`를 쓰면 `"native"`, `fallback_import`를 쓰면 `"classic_fallback"` | (선택) `kind` |

`kind`는 평가의 **classic 의존 비율**과 같은 구분입니다. 1번도 같은 문제를 보고 있다는 뜻이라, report `changes[]`에 `kind`를 선택 필드로 넣어 주면 화면에서 "classic 우회" 표시를 바로 할 수 있습니다.

## 한 줄 요약

**symbol_map은 "옛 위치 → 새 위치" 이사 목록이고, 모든 줄에는 근거 ID가 붙어야 합니다.**
같은 근거 ID를 Qdrant 조각에도 붙이면, 3번은 그 ID로 근거를 확인하고(verifier (a)), 화면은 근거 링크를 보여 주고, 평가는 근거 일치율을 셀 수 있습니다.

| 누가 | symbol_map · 근거 ID를 어떻게 쓰나 |
|---|---|
| 2번 retriever | 옛 심볼로 새 위치를 바로 찾기 (정확 조회), 부족하면 Qdrant 검색 |
| 3번 rewriter | 변경마다 `evidence_id`를 붙여 report에 넣기 |
| 3번 verifier (a) | 그 `evidence_id`가 실제 검색 결과(Qdrant · symbol_map)에 있는지 확인 |
| 4번 화면 | `evidence_url`로 "문서 열기" 링크 |
| 4번 평가 | 테스트셋 30문제의 옛 심볼을 symbol_map이 얼마나 덮는지, 정답 방향과 같은지 대조 |

## 1. symbol_map.json 모양

```json
{
  "symbol_map_version": "1.0",
  "langchain_version": "1.4.4",
  "generated_at": "2026-10-13",
  "symbols": [
    {
      "old": "langchain.chat_models.ChatOpenAI",
      "status": "moved",
      "new_import": "from langchain_openai import ChatOpenAI",
      "replacement": null,
      "replacement_imports": [],
      "fallback_import": null,
      "package": "langchain-openai",
      "evidence_ids": ["v1-migration#chat-models-01"]
    },
    {
      "old": "langchain.chains.LLMChain",
      "status": "removed",
      "new_import": null,
      "replacement": "LCEL로 연결: chain = prompt | llm | StrOutputParser()",
      "replacement_imports": ["from langchain_core.output_parsers import StrOutputParser"],
      "fallback_import": "from langchain_classic.chains import LLMChain",
      "package": "langchain-core",
      "evidence_ids": ["v1-migration#llmchain-03", "v1-migration#classic-07"]
    }
  ]
}
```

전체 예시 (10개, 실제 환경에서 확인 완료): [symbol_map.example.json](contracts/symbol_map.example.json)

### 필드

| 필드 | 형식 | 설명 |
|---|---|---|
| `symbol_map_version` | `"1.0"` | 모양이 바뀌면 올림 |
| `langchain_version` | 문자열 | 어느 버전 기준인지 (검증 환경과 같아야 함) |
| `old` | 점 경로 | 옛 위치. `from langchain.chat_models import ChatOpenAI` → `langchain.chat_models.ChatOpenAI` |
| `status` | `moved` / `removed` / `unchanged` | 아래 표 |
| `new_import` | import 한 줄 또는 null | 새 위치 (`moved`, `unchanged`는 필수) |
| `replacement` | 문자열 또는 null | 없어진 것을 무엇으로 바꾸는지 설명 (`removed`) |
| `replacement_imports` | import 목록 | 바꾼 방식에 필요한 import (없으면 `[]`) |
| `fallback_import` | import 한 줄 또는 null | `langchain_classic`으로 우회하는 길 (있으면). 평가에서는 "classic 의존"으로 따로 셈 |
| `package` | 문자열 또는 null | 새 위치를 쓰려면 설치할 패키지 |
| `evidence_ids` | 근거 ID 목록 (1개 이상) | **근거 없는 줄은 넣지 않습니다** |

### `status` 값

| 값 | 뜻 | 예 |
|---|---|---|
| `moved` | 같은 이름이 다른 위치로 이사 | `ChatOpenAI` → `langchain_openai` |
| `removed` | 없어짐. 다른 방식으로 바꿔야 함 | `LLMChain` → LCEL, `initialize_agent` → `create_agent` |
| `unchanged` | 그대로 써도 됨 | `langchain.tools.tool` |

## 2. 근거 ID 규칙

**모양: `문서#섹션-번호`** (영어 소문자, 숫자, 하이픈만 · 번호는 두 자리 이상)

```text
v1-migration#chat-models-01
v1-migration#llmchain-03
release-notes-1-4#agents-12
```

- **같은 근거 조각에는 어디서나 같은 ID**를 씁니다. symbol_map의 `evidence_ids`, Qdrant 조각의 payload, 3번 report의 `evidence_id`가 모두 같은 문자열이어야 verifier (a)가 확인할 수 있습니다.
- ID는 한 번 정하면 바꾸지 않습니다. 문서를 다시 청킹해도 같은 섹션이면 같은 ID를 유지해 주세요.

### Qdrant 조각 payload (3번이 근거 링크를 만들 때 필요)

```json
{
  "evidence_id": "v1-migration#llmchain-03",
  "title": "LangChain v1 migration guide",
  "section": "Legacy chains",
  "url": "https://docs.langchain.com/oss/python/migrate/langchain-v1#…",
  "chunk_type": "before_after",
  "langchain_version": "1.4.4",
  "text": "…조각 내용…"
}
```

| 필드 | 쓰는 곳 |
|---|---|
| `evidence_id` | verifier (a) 확인, report `evidence_id` |
| `url` | report `evidence_url` → 화면 "문서 열기" (가능하면 섹션 앵커 `#…`까지) |
| `chunk_type` | `text`(설명) / `before_after`(구 코드 → 신 코드 예시) |

## 3. 지켜 줄 규칙

1. **실제로 확인한 것만 넣습니다.** `new_import`, `replacement_imports`, `fallback_import`는 최신 검증 환경에서 실제로 import되어야 합니다. 아래 검사기가 직접 실행해서 확인합니다.
2. **`fallback_import`는 하나씩 확인합니다.** 여러 이름을 한 줄로 가져오면, 하나만 안 돼도 전부 안 되는 것처럼 보입니다. (실제로 4번이 처음에 이 실수를 했습니다: `langchain_classic.agents`에서 `initialize_agent`는 되고 `load_tools`만 안 됩니다.)
3. **`old` 하나에 한 줄.** 같은 `old`가 두 번 나오면 안 됩니다.
4. **`langchain_version`은 검증 환경과 같은 버전**으로 만듭니다. (지금 기준 1.4.4, `eval/requirements-verify.txt`로 고정 예정)

## 4. 맞는지 확인하는 방법

```bash
cd eval
python check_symbol_map.py symbol_map.json                                          # 모양만
python check_symbol_map.py symbol_map.json --py verify-env/Scripts/python.exe       # 실제 import 로 확인
python check_symbol_map.py symbol_map.json --py verify-env/Scripts/python.exe --testset testset.json   # 테스트셋과 대조
```

검사기가 확인하는 것:

| 검사 | 예 |
|---|---|
| 모양 | 필드 빠짐, `status` 오타, 근거 ID 규칙 위반, 근거 없는 줄 |
| 실제 실행 | 새 위치가 안 됨, classic 우회가 안 됨, `moved`인데 옛 위치가 아직 됨(→ `unchanged`가 맞음) |
| 테스트셋 대조 | 테스트셋 옛 심볼 57종(등장 114번)을 얼마나 덮는지, 새 위치가 테스트셋 정답 방향과 같은지, 빠진 심볼 목록 |

예시 10개로 돌린 결과: 모양 · 실행 모두 통과, 테스트셋 대조 **10/57종 · 등장 기준 50/114**, 정답 방향과 다른 것 0개. 빠진 것 중 많이 나오는 순서는 `AgentExecutor`(6문제), `OpenAIEmbeddings`(4), `ChatPromptTemplate`(4), `MessagesPlaceholder`(3)입니다.

## 5. 정할 것 (2번 답변 필요)

| # | 질문 | 4번 제안 |
|---|---|---|
| 1 | symbol_map은 어떻게 만드나요? (가이드에서 자동 추출 / 손으로 정리 / 둘 다) | 가이드 · 릴리스 노트에서 뽑고, 검사기로 확인 |
| 2 | 근거 ID 규칙(`문서#섹션-번호`)을 Qdrant payload에도 그대로 쓸 수 있나요? | 예 |
| 3 | 테스트셋 옛 심볼 57종을 목표로 해도 될까요? | 많이 나오는 순서로 먼저 (위 4장 목록) |
| 4 | Qdrant payload에 `url`을 섹션 앵커까지 넣을 수 있나요? | 가능하면 앵커까지, 안 되면 문서 주소 |
| 5 | `symbol_map.json`은 저장소 어디에 두나요? | `data/symbol_map.json` |

## 6. 2번에게 보낼 메시지

> 2번님, symbol_map이랑 근거 ID 모양 맞추려고 합의안 만들었어요!
> symbol_map은 "옛 위치 → 새 위치" 이사 목록인데, **줄마다 근거 ID를 꼭 붙이고**, 같은 ID를 Qdrant 조각 payload에도 넣어 주시면 3번 verifier가 근거를 확인하고 제 화면이 근거 링크를 보여 줄 수 있어요.
> 👉 https://github.com/SKN35shimsungwook/langchain-migration-helper/blob/main/docs/symbol_map_합의안.md (예시 10개 포함)
> 만든 파일은 `python check_symbol_map.py symbol_map.json --py ... --testset testset.json`으로 돌리면 **새 위치가 진짜 import되는지**랑 **테스트셋 57개 심볼을 얼마나 덮는지**까지 바로 나와요.
> 팁 하나: classic 우회는 이름을 하나씩 확인해 주세요. 한 줄로 여러 개 가져오면 하나만 안 돼도 전부 실패처럼 보여서, 저도 처음에 착각했어요 😅
> 5장 "정할 것" 답 주시면 확정할게요 🙏
