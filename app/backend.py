"""화면이 파이프라인을 부르는 곳.

백엔드(1번 API)가 준비되기 전에는 테스트셋으로 만든 가짜 응답(mock)을 돌려준다.
API 주소(예: http://localhost:8000)를 환경 변수 MIGRATION_API_URL 에 넣으면
POST {주소}/migrate 로 실제 백엔드를 부른다. 호출 규칙은 docs/API_합의안.md.

report 출력 모양 (3번 report 노드와 합의한 형식) — docs/출력모양_합의안.md
{
  "contract_version": "1.0",
  "original_code": "...",
  "migrated_code": "...",
  "changes": [
    {"old": "구 코드 한 줄", "new": "새 코드 한 줄", "reason": "바꾼 이유",
     "evidence_id": "근거 ID", "evidence_url": "근거 문서 링크", "evidence_ok": true}
  ],
  "verification": {"success": true, "fail_stage": null, "error": null, "checked_attributes": []},
  "attempts": 2,
  "attempt_log": [
    {"attempt": 1, "fail_stage": "import", "error_type": "ModuleNotFoundError", "target": "langchain.chains", "message": "..."},
    {"attempt": 2, "fail_stage": null, "error_type": null, "target": null, "message": null}
  ]
}
가짜 응답에는 "mock": true 가 추가로 붙는다.
"""

import ast
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTSET = ROOT / "eval" / "testset.json"
GUIDE_URL = "https://docs.langchain.com/oss/python/migrate/langchain-v1"


def load_testset() -> list[dict]:
    return json.loads(TESTSET.read_text(encoding="utf-8"))


class ApiError(Exception):
    """API가 에러를 돌려주거나 연결이 안 될 때 (docs/API_합의안.md 4장)."""


def api_base() -> str | None:
    """1번 API 주소 (예: http://localhost:8000). 없으면 가짜 응답을 쓴다."""
    url = os.environ.get("MIGRATION_API_URL", "").strip().rstrip("/")
    return url or None


def _call(method: str, path: str, body: dict | None = None, timeout: float = 10) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(api_base() + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))["error"]
            raise ApiError(f"{e.code} {err['code']}: {err['message']}") from None
        except (ValueError, KeyError, TypeError):
            raise ApiError(f"{e.code} 에러 (응답 모양이 합의안과 다름)") from None
    except (urllib.error.URLError, TimeoutError) as e:
        raise ApiError(f"API에 연결할 수 없음: {getattr(e, 'reason', e)}") from None


def api_info() -> dict | None:
    """GET /info — 모델, 최대 시도, 샌드박스 버전. 가짜 응답 모드면 None."""
    return _call("GET", "/info") if api_base() else None


def migrate(code: str, testset: list[dict]) -> dict:
    """POST /migrate — 응답은 docs/출력모양_합의안.md 의 report."""
    if api_base():
        timeout = float(os.environ.get("MIGRATION_API_TIMEOUT", "180"))
        return _call("POST", "/migrate", {"code": code}, timeout=timeout)
    return _mock(code, testset)


def _import_lines(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]


def _mock(code: str, testset: list[dict]) -> dict:
    """테스트셋에 있는 코드면 정답 방향 import 로 바꾼 가짜 결과를 만든다."""
    item = next((t for t in testset if t["old_code"].strip() == code.strip()), None)
    if item is None:
        return {"contract_version": "1.0", "original_code": code, "migrated_code": code, "changes": [],
                "verification": {"success": False, "fail_stage": "mock",
                                 "error": "가짜 응답은 테스트셋 예제만 변환합니다. 실제 백엔드가 연결되면 모든 코드를 변환합니다.",
                                 "checked_attributes": []},
                "attempts": 0, "attempt_log": [], "mock": True}

    old_imports = _import_lines(item["old_code"])
    new_imports = [l for l in item["target_imports"].splitlines() if l.strip()]
    body = "\n".join(l for l in item["old_code"].splitlines() if l.strip() not in old_imports).strip("\n")
    migrated = "\n".join(new_imports) + "\n\n" + body

    changes = []
    for i, old in enumerate(old_imports):
        new = new_imports[i] if i < len(new_imports) else "(삭제 · 다른 줄로 대체)"
        changes.append({"old": old, "new": new, "reason": item["why_broken"],
                        "evidence_id": f"{item['id']}-{i + 1}", "evidence_url": GUIDE_URL, "evidence_ok": True})

    # 난이도가 높을수록 한 번 더 고친 것처럼 보여 준다 (화면 확인용)
    if item["difficulty"] == "easy":
        log = [{"attempt": 1, "fail_stage": None, "error_type": None, "target": None, "message": None}]
    else:
        first = old_imports[-1] if old_imports else ""
        log = [{"attempt": 1, "fail_stage": "import", "error_type": "ModuleNotFoundError", "target": first,
                "message": f"{first} 에서 가져올 수 없음"},
               {"attempt": 2, "fail_stage": None, "error_type": None, "target": None, "message": None}]
    return {"contract_version": "1.0", "original_code": item["old_code"], "migrated_code": migrated, "changes": changes,
            "verification": {"success": True, "fail_stage": None, "error": None, "checked_attributes": []},
            "attempts": len(log), "attempt_log": log, "mock": True, "example_id": item["id"]}
