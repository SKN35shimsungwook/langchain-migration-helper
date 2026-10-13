"""우리 시스템(B) 실험: 테스트 코드 30개를 파이프라인에 넣고, report 를 평가 결과로 바꿔 저장한다.

3번은 report 만 합의한 모양으로 돌려주면 된다. 평가용 계산은 여기서 한다.
판정은 baseline(A)과 같은 verify.py 로 다시 한다 (EVAL_RULES 5장 '같은 판정기').

실행:
    $env:MIGRATION_FUNC="src.graph.supervisor:run_migration"   (팀 그래프 함수, 기본안. 규칙은 docs/API_합의안.md)
    또는 $env:MIGRATION_API_URL="http://localhost:8000"        (HTTP로 부를 때)
    python run_system.py --py verify-env/Scripts/python.exe --model [모델명]
    python run_system.py --py verify-env/Scripts/python.exe --mock      # API 없이 흐름만 확인 (화면용 가짜 응답 사용)
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from check_contract import check
from verify import judge

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "app"))
from backend import ApiError, _mock, api_info, func_target, migrate, mode  # noqa: E402


def to_result(item: dict, report: dict, py: str, model: str) -> dict:
    """report 하나를 EVAL_RULES 7장 결과 형식으로 바꾼다."""
    problems = check(report)
    v = judge(report.get("migrated_code", ""), py)
    log = report.get("attempt_log", [])
    changes = report.get("changes", [])
    return {
        "id": item["id"], "difficulty": item["difficulty"], "system": "B", "model": model,
        **v,
        "attempts": report.get("attempts", len(log)),
        "first_try_success": bool(log) and log[0].get("fail_stage") is None,
        "evidence": {"total": len(changes), "valid": sum(bool(c.get("evidence_ok")) for c in changes)},
        "attempt_log": log,
        "pipeline_verification": report.get("verification"),
        "contract_problems": problems,
        "migrated_code": report.get("migrated_code", ""),
    }


def main():
    ap = argparse.ArgumentParser(description="우리 시스템(B) 실험")
    ap.add_argument("--py", required=True, help="검증 환경의 python 경로")
    ap.add_argument("--model", default="unknown", help="파이프라인이 쓴 모델 (A와 같아야 함)")
    ap.add_argument("--testset", default=str(HERE / "testset.json"))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--mock", action="store_true", help="API 없이 가짜 응답으로 흐름만 확인")
    a = ap.parse_args()

    items = json.loads(Path(a.testset).read_text(encoding="utf-8"))
    if a.limit:
        items = items[: a.limit]
    tag = "mock" if a.mock else a.model
    out = HERE / "results" / f"B_{tag}_{date.today()}.json"
    out.parent.mkdir(exist_ok=True)
    results = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
    done = {r["id"] for r in results}

    if not a.mock and mode() == "func":
        print(f"팀 그래프 직접 호출: {func_target()} · 모델은 --model({a.model})과 같은지 직접 확인하세요 (EVAL_RULES 5장).")
    elif not a.mock:
        try:
            info = api_info()
        except ApiError as e:
            sys.exit(f"API에 연결할 수 없습니다. 1번 API가 켜져 있는지, 주소가 맞는지 확인하세요.\n  ({e})")
        if info is None:
            sys.exit("MIGRATION_FUNC(팀 그래프 함수)나 MIGRATION_API_URL(API 주소)이 없습니다. 둘 중 하나를 넣거나 --mock 으로 실행하세요.")
        print(f"API 정보: 모델 {info.get('model')} · 최대 {info.get('max_attempts')}회 · 샌드박스 {info.get('sandbox')}")
        if info.get("model") != a.model:
            print(f"[주의] --model({a.model})과 API 모델({info.get('model')})이 다릅니다. A와 같은 모델인지 확인하세요 (EVAL_RULES 5장).")

    for i, item in enumerate(items, 1):
        if item["id"] in done:
            continue
        print(f"[{i}/{len(items)}] {item['id']} ...", end=" ", flush=True)
        try:
            report = _mock(item["old_code"], items) if a.mock else migrate(item["old_code"], items)
            r = to_result(item, report, a.py, tag)
        except ApiError as e:
            r = {"id": item["id"], "difficulty": item["difficulty"], "system": "B", "model": tag,
                 "success": False, "fail_stage": "api", "error": str(e), "attempts": 0,
                 "first_try_success": False, "evidence": {"total": 0, "valid": 0}, "attempt_log": [],
                 "contract_problems": [], "migrated_code": ""}
        results.append(r)
        out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        note = f" · 형식 문제 {len(r['contract_problems'])}개" if r["contract_problems"] else ""
        print(("성공" if r["success"] else f"실패 ({r['fail_stage']})") + f" · {r['attempts']}회{note}")

    n = len(results)
    ok = sum(r["success"] for r in results)
    first = sum(r["first_try_success"] for r in results)
    ev_t = sum(r["evidence"]["total"] for r in results)
    ev_v = sum(r["evidence"]["valid"] for r in results)
    print(f"\n결과 파일: {out}")
    print(f"최종 성공률: {ok}/{n} · 1회차 성공: {first}/{n} · 근거 일치: {ev_v}/{ev_t}")
    bad = [r["id"] for r in results if r["contract_problems"]]
    if bad:
        print(f"[확인 필요] 합의한 모양과 다른 report: {bad} → python check_contract.py 로 자세히 보기")


if __name__ == "__main__":
    main()
