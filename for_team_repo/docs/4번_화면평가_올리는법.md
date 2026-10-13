# 4번(화면 · 평가) 파일 안내

> 이 폴더는 개인 저장소 [langchain-migration-helper](https://github.com/SKN35shimsungwook/langchain-migration-helper)의 `tools/make_team_copy.py`가 만든 **팀 저장소용 사본**입니다.
> 원본은 개인 저장소의 `app/`, `eval/`, `docs/`이고, 이 폴더를 직접 고치지 않습니다.

## 들어 있는 것 (팀 저장소 구조 그대로)

```text
SKN35-3rd-4Team/
├── app.py                     ← 화면 (Streamlit). 지금의 Hello World 자리
├── src/ui/
│   ├── __init__.py
│   └── backend.py             ← 화면이 팀 그래프를 부르는 곳 (함수 → HTTP → 가짜 응답)
├── eval/                      ← 평가 전체
│   ├── EVAL_RULES.md  testset.json  verify.py
│   ├── check_testset.py  run_baseline.py  run_system.py  make_charts.py
│   └── check_contract.py  check_symbol_map.py
└── docs/
    ├── 4번_화면평가_올리는법.md  ← 이 문서
    ├── 출력모양_합의안.md  API_합의안.md  symbol_map_합의안.md
    └── contracts/             ← 예시 JSON, 연습용 API 서버
```

팀 저장소에 이미 있는 파일 중 바뀌는 것은 **`app.py` 하나**입니다(지금은 `print('Hello World!')`). 나머지는 모두 새 파일입니다. `src/agents`, `src/graph`, `src/rag`, `data/`는 건드리지 않습니다.

## 팀 저장소에 올리는 순서 (4번이 직접, 1번 확인 후)

PowerShell에서는 `&&`를 쓸 수 없으니 **한 줄씩** 실행합니다. 팀 저장소 폴더에서:

```powershell
git switch <4번 브랜치>
git pull origin dev
Copy-Item -Recurse -Force <개인 저장소>\for_team_repo\* .
uv add streamlit
git status
```

`git status`로 바뀐 파일이 위 목록뿐인지 확인한 뒤 커밋하고, dev로 PR을 올립니다.

## 실행

```powershell
uv run streamlit run app.py
```

| 연결 방법 | 설정 |
|---|---|
| 팀 그래프 함수 (기본안) | `$env:MIGRATION_FUNC="src.graph.supervisor:run_migration"` |
| HTTP (선택) | `$env:MIGRATION_API_URL="http://localhost:8000"` |
| 아무것도 없음 | 테스트셋 예제로 가짜 응답 |

평가는 `eval` 폴더에서 실행합니다. 자세한 명령은 개인 저장소 README 8-3장에 있습니다.
