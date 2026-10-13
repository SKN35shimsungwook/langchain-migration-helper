"""테스트셋 후보가 최신 LangChain 환경에서 정말 깨지는지 확인한다.

항목마다 아래 두 가지를 검사한다.
  1. old_code 의 import 문이 검증 환경에서 실패하는가   (실패해야 테스트 의미가 있음)
  2. target_imports 가 검증 환경에서 성공하는가        (정답 방향이 실제로 존재하는지)

준비 (처음 한 번만):
    uv venv verify-env --python 3.12
    uv pip install --python verify-env/Scripts/python.exe langchain langchain-core langchain-openai langchain-community langchain-classic langgraph
    verify-env/Scripts/python.exe -m pip freeze > requirements-verify.txt

실행:
    python check_testset.py testset_sample.json --py verify-env/Scripts/python.exe
    python check_testset.py testset_sample.json --py verify-env/Scripts/python.exe --write   # 결과를 파일에 기록
"""

import argparse
import ast
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REQUIRED = ["id", "difficulty", "old_code", "why_broken", "target_imports"]
DIFFICULTIES = ["easy", "medium", "hard"]


def import_lines(code: str) -> list[str]:
    """코드에서 import 문만 뽑는다. 함수 안에 있는 import 도 포함."""
    tree = ast.parse(code)
    return [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]


def run(py: str, src: str, timeout: int) -> tuple[bool, str]:
    """검증 환경 파이썬으로 src 를 실행한다. (성공 여부, 마지막 에러 줄)"""
    try:
        p = subprocess.run([py, "-W", "ignore", "-c", src], capture_output=True,
                           text=True, timeout=timeout, encoding="utf-8")
    except subprocess.TimeoutExpired:
        return False, f"Timeout ({timeout}s)"
    err = (p.stderr.strip().splitlines() or [""])[-1]
    return p.returncode == 0, err


def check_item(item: dict, py: str, timeout: int) -> dict:
    missing = [k for k in REQUIRED if not item.get(k)]
    if missing:
        return {"ok": False, "problem": f"필수 필드 없음: {missing}"}
    if item["difficulty"] not in DIFFICULTIES:
        return {"ok": False, "problem": f"difficulty 는 {DIFFICULTIES} 중 하나여야 함"}

    try:
        lines = import_lines(item["old_code"])
    except SyntaxError as e:
        return {"ok": False, "problem": f"old_code 문법 오류: {e}"}
    if not lines:
        return {"ok": False, "problem": "old_code 에 import 문이 없음"}

    # 줄마다 따로 실행해서 어느 줄이 깨지는지 기록
    failing = []
    for line in lines:
        ok, err = run(py, line, timeout)
        if not ok:
            failing.append({"line": line, "error": err})

    target_ok, target_err = run(py, item["target_imports"], timeout)

    problems = []
    if not failing:
        problems.append("old_code 가 최신 환경에서 깨지지 않음 → 테스트로 쓸 수 없음")
    if not target_ok:
        problems.append(f"target_imports 가 실패함 → 정답 방향 확인 필요 ({target_err})")

    return {"ok": not problems, "problem": " / ".join(problems),
            "failing": failing, "new_fails": bool(failing), "target_ok": target_ok}


def main():
    ap = argparse.ArgumentParser(description="테스트셋 후보 검증")
    ap.add_argument("testset", help="검사할 JSON 파일")
    ap.add_argument("--py", required=True, help="검증 환경의 python 경로")
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--write", action="store_true", help="verified_new_fails 결과를 파일에 기록")
    a = ap.parse_args()

    path = Path(a.testset)
    items = json.loads(path.read_text(encoding="utf-8"))

    dup = [k for k, v in Counter(i.get("id") for i in items).items() if v > 1]
    if dup:
        print(f"[경고] 중복된 id: {dup}")

    passed = 0
    for item in items:
        r = check_item(item, a.py, a.timeout)
        mark = "PASS" if r["ok"] else "FAIL"
        print(f"[{mark}] {item.get('id', '?')} ({item.get('difficulty', '?')})")
        for f in r.get("failing", []):
            print(f"        깨지는 줄: {f['line']}")
            print(f"          -> {f['error'][:100]}")
        if r["problem"]:
            print(f"        문제: {r['problem']}")
        if "new_fails" in r:
            item["verified_new_fails"] = r["new_fails"]
        passed += r["ok"]

    counts = Counter(i.get("difficulty") for i in items)
    print("\n=== 요약 ===")
    print(f"통과: {passed} / {len(items)}")
    print("난이도별 개수: " + ", ".join(f"{d} {counts.get(d, 0)}" for d in DIFFICULTIES)
          + "  (목표: 각 10개)")

    if a.write:
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"결과를 {path} 에 기록했습니다.")

    sys.exit(0 if passed == len(items) else 1)


if __name__ == "__main__":
    main()
