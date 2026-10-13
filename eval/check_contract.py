"""report 출력이 3번과 합의한 모양(docs/출력모양_합의안.md)인지 검사한다.

    python check_contract.py ../docs/contracts/report.example.json
    python check_contract.py report.json --py verify-env/Scripts/python.exe   # 판정 결과가 verify.py와 같은지도 확인

--py 를 주면 migrated_code 를 verify.py 로 다시 판정해서, report 의 verification 과 결과가 같은지 비교한다.
(3번 verifier 와 4번 평가 판정기가 같은 기준인지 확인하는 용도)
"""

import argparse
import json
import sys
from pathlib import Path

FAIL_STAGES = {None, "syntax", "import", "attribute", "evidence", "timeout"}


def check(report: dict) -> list[str]:
    """문제 목록을 돌려준다. 빈 목록이면 합의한 모양이다."""
    p = []

    def need(obj, key, types, where):
        if key not in obj:
            p.append(f"{where}: '{key}' 가 없음")
            return None
        if not isinstance(obj[key], types):
            p.append(f"{where}: '{key}' 의 형식이 {types} 가 아님")
        return obj[key]

    need(report, "contract_version", str, "report")
    need(report, "target_version", str, "report")  # 1.1 에서 추가 (목표 버전 선택)
    need(report, "original_code", str, "report")
    need(report, "migrated_code", str, "report")

    changes = need(report, "changes", list, "report") or []
    for i, c in enumerate(changes):
        w = f"changes[{i}]"
        for k in ("old", "new", "reason", "evidence_id"):
            need(c, k, str, w)
        need(c, "evidence_url", (str, type(None)), w)
        need(c, "evidence_ok", bool, w)

    v = need(report, "verification", dict, "report") or {}
    need(v, "success", bool, "verification")
    if v.get("fail_stage") not in FAIL_STAGES:
        p.append(f"verification: fail_stage '{v.get('fail_stage')}' 는 {sorted(s for s in FAIL_STAGES if s)} 중 하나 또는 null 이어야 함")
    need(v, "error", (str, type(None)), "verification")
    need(v, "checked_attributes", list, "verification")
    if v.get("success") is True and v.get("fail_stage") is not None:
        p.append("verification: success 가 true 인데 fail_stage 가 있음")

    attempts = need(report, "attempts", int, "report")
    log = need(report, "attempt_log", list, "report") or []
    if isinstance(attempts, int) and len(log) != attempts:
        p.append(f"attempt_log 개수({len(log)})와 attempts({attempts})가 다름")
    for i, a in enumerate(log):
        w = f"attempt_log[{i}]"
        if a.get("attempt") != i + 1:
            p.append(f"{w}: attempt 는 {i + 1} 이어야 함")
        if a.get("fail_stage") not in FAIL_STAGES:
            p.append(f"{w}: fail_stage '{a.get('fail_stage')}' 가 허용 값이 아님")
        for k in ("error_type", "target", "message"):
            if k not in a:
                p.append(f"{w}: '{k}' 가 없음 (없으면 null)")
    if log and v.get("success") is True and log[-1].get("fail_stage") is not None:
        p.append("마지막 시도가 실패인데 verification.success 가 true 임")
    return p


def main():
    ap = argparse.ArgumentParser(description="report 출력 모양 검사")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--py", help="검증 환경 python. 주면 verify.py 로 다시 판정해 비교")
    a = ap.parse_args()

    judge = None
    if a.py:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from verify import judge

    bad = 0
    for f in a.files:
        report = json.loads(Path(f).read_text(encoding="utf-8"))
        problems = check(report)
        if judge and not problems:
            j = judge(report["migrated_code"], a.py)
            v = report["verification"]
            same = j["success"] == v["success"] and (j["success"] or j["fail_stage"] == v["fail_stage"])
            if not same:
                problems.append(f"판정 불일치: report 는 success={v['success']}, fail_stage={v['fail_stage']} / "
                                f"verify.py 는 success={j['success']}, fail_stage={j['fail_stage']} ({j['error']})")
        print(f"[{'PASS' if not problems else 'FAIL'}] {f}")
        for x in problems:
            print("   -", x)
        bad += bool(problems)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
