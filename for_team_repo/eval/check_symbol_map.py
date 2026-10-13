"""2번의 symbol_map.json 이 합의한 모양(docs/symbol_map_합의안.md)인지, 실제로 맞는지 검사한다.

    python check_symbol_map.py ../docs/contracts/symbol_map.example.json
    python check_symbol_map.py symbol_map.json --py verify-env/Scripts/python.exe        # 실제 import 로 확인
    python check_symbol_map.py symbol_map.json --py verify-env/Scripts/python.exe --testset testset.json   # 테스트셋과 대조

확인하는 것
  1. 모양: 필드, status 값, 근거 ID 규칙
  2. (--py) 실행: 새 위치 · 대체 import · classic 우회가 최신 환경에서 실제로 되는지,
                  옛 위치는 정말 깨지는지 (unchanged 는 그대로 되는지)
  3. (--testset) 대조: 테스트셋 30문제의 옛 심볼을 symbol_map 이 얼마나 덮는지, 정답 방향과 같은지
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

STATUSES = {"moved", "removed", "unchanged"}
EVIDENCE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*#[a-z0-9-]+-\d{2,}$")


def check_shape(m: dict) -> list[str]:
    p = []
    for k, t in (("symbol_map_version", str), ("langchain_version", str), ("symbols", list)):
        if not isinstance(m.get(k), t):
            p.append(f"맨 위 '{k}' 가 없거나 형식이 다름")
    seen = set()
    for i, s in enumerate(m.get("symbols", [])):
        w = f"symbols[{i}] ({s.get('old', '?')})"
        if not isinstance(s.get("old"), str) or "." not in s.get("old", ""):
            p.append(f"{w}: old 는 'langchain.chat_models.ChatOpenAI' 같은 점 경로여야 함")
        if s.get("old") in seen:
            p.append(f"{w}: 같은 old 가 두 번 나옴")
        seen.add(s.get("old"))
        st = s.get("status")
        if st not in STATUSES:
            p.append(f"{w}: status 는 {sorted(STATUSES)} 중 하나여야 함")
        for k in ("new_import", "replacement", "fallback_import", "package"):
            if k not in s:
                p.append(f"{w}: '{k}' 가 없음 (없으면 null)")
        if not isinstance(s.get("replacement_imports"), list):
            p.append(f"{w}: replacement_imports 는 목록이어야 함 (없으면 [])")
        if st in ("moved", "unchanged") and not s.get("new_import"):
            p.append(f"{w}: {st} 이면 new_import 가 있어야 함")
        if st == "removed" and not (s.get("replacement") or s.get("fallback_import")):
            p.append(f"{w}: removed 이면 replacement 나 fallback_import 중 하나는 있어야 함")
        ids = s.get("evidence_ids")
        if not isinstance(ids, list) or not ids:
            p.append(f"{w}: evidence_ids 가 비어 있음 (근거 없이 바꾸면 안 됨)")
        else:
            bad = [x for x in ids if not EVIDENCE_ID.match(str(x))]
            if bad:
                p.append(f"{w}: 근거 ID 규칙(문서#섹션-번호, 소문자)과 다름: {bad}")
    return p


def old_import_line(old: str) -> str:
    mod, name = old.rsplit(".", 1)
    return f"from {mod} import {name}"


def runs(py: str, code: str) -> tuple[bool, str]:
    r = subprocess.run([py, "-W", "ignore", "-c", code], capture_output=True, text=True, timeout=60, encoding="utf-8")
    return r.returncode == 0, (r.stderr.strip().splitlines() or [""])[-1]


def check_runtime(m: dict, py: str) -> list[str]:
    p = []
    for s in m.get("symbols", []):
        w = s.get("old")
        lines = ([s["new_import"]] if s.get("new_import") else []) + list(s.get("replacement_imports") or [])
        for line in lines:
            ok, err = runs(py, line)
            if not ok:
                p.append(f"{w}: 새 위치가 최신 환경에서 안 됨 → {line} ({err[:80]})")
        if s.get("fallback_import"):
            ok, err = runs(py, s["fallback_import"])
            if not ok:
                p.append(f"{w}: classic 우회가 안 됨 → {s['fallback_import']} ({err[:80]})")
        ok, _ = runs(py, old_import_line(w))
        if s.get("status") == "unchanged" and not ok:
            p.append(f"{w}: unchanged 인데 옛 위치가 깨짐")
        if s.get("status") in ("moved", "removed") and ok:
            p.append(f"{w}: {s['status']} 인데 옛 위치가 아직 됨 (unchanged 가 맞을 수 있음)")
    return p


def testset_symbols(testset: list[dict]) -> Counter:
    c = Counter()
    for t in testset:
        for n in ast.walk(ast.parse(t["old_code"])):
            if isinstance(n, ast.ImportFrom):
                c.update(f"{n.module}.{a.name}" for a in n.names)
    return c


def compare_testset(m: dict, testset: list[dict]) -> None:
    used = testset_symbols(testset)
    by_old = {s["old"]: s for s in m.get("symbols", [])}
    targets = {}
    for t in testset:
        for n in ast.walk(ast.parse(t["target_imports"])):
            if isinstance(n, ast.ImportFrom):
                for a in n.names:
                    targets.setdefault(a.name, set()).add(n.module)
    covered = [o for o in used if o in by_old]
    weight = sum(used[o] for o in covered)
    print(f"\n=== 테스트셋 대조 ===")
    print(f"옛 심볼 덮은 비율: {len(covered)}/{len(used)} 종류 · 등장 횟수 기준 {weight}/{sum(used.values())}")
    agree, differ = [], []
    for o in covered:
        s = by_old[o]
        if s["status"] != "moved":
            continue
        new_mod = ast.parse(s["new_import"]).body[0].module
        name = o.rsplit(".", 1)[1]
        (agree if new_mod in targets.get(name, set()) else differ).append(f"{o} → {new_mod} (테스트셋: {sorted(targets.get(name, []))})")
    print(f"정답 방향과 같음 (moved): {len(agree)}개")
    for d in differ:
        print(f"  [다름] {d}")
    missing = sorted((o for o in used if o not in by_old), key=lambda o: -used[o])
    if missing:
        print("symbol_map 에 없는 옛 심볼 (많이 나오는 순):")
        for o in missing[:15]:
            print(f"  - {o} ({used[o]}문제)")
        if len(missing) > 15:
            print(f"  … 외 {len(missing) - 15}개")


def main():
    ap = argparse.ArgumentParser(description="symbol_map 검사")
    ap.add_argument("file")
    ap.add_argument("--py", help="검증 환경 python. 주면 실제 import 로 확인")
    ap.add_argument("--testset", help="테스트셋과 대조")
    a = ap.parse_args()

    m = json.loads(Path(a.file).read_text(encoding="utf-8"))
    problems = check_shape(m)
    if a.py and not problems:
        problems += check_runtime(m, a.py)
    print(f"[{'PASS' if not problems else 'FAIL'}] {a.file} · 심볼 {len(m.get('symbols', []))}개")
    for x in problems:
        print("   -", x)
    if a.testset:
        compare_testset(m, json.loads(Path(a.testset).read_text(encoding="utf-8")))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
