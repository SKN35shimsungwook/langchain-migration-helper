"""4번 파일을 팀 저장소(SKN35-3rd-4Team)와 같은 폴더 구조로 for_team_repo/ 에 복사한다.

원본은 이 저장소의 app/, eval/, docs/ 하나뿐이고, for_team_repo/ 는 이 스크립트가 만드는 사본이다.
원본을 고친 뒤에는 이 스크립트를 다시 실행하면 사본도 같아진다. (for_team_repo/ 를 직접 고치지 않기)

    python tools/make_team_copy.py

팀 저장소에 올릴 때는 for_team_repo/ 안의 내용을 팀 저장소 폴더에 그대로 덮어 복사하면 된다.
팀 저장소에 이미 있는 파일(app.py 제외)은 건드리지 않도록 새 파일만 만든다.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "for_team_repo"

# (원본, 팀 저장소 안 위치)
FILES = [
    ("app/streamlit_app.py", "app.py"),
    ("app/backend.py", "src/ui/backend.py"),
    ("eval/EVAL_RULES.md", "eval/EVAL_RULES.md"),
    ("eval/testset.json", "eval/testset.json"),
    ("eval/verify.py", "eval/verify.py"),
    ("eval/check_testset.py", "eval/check_testset.py"),
    ("eval/run_baseline.py", "eval/run_baseline.py"),
    ("eval/run_system.py", "eval/run_system.py"),
    ("eval/make_charts.py", "eval/make_charts.py"),
    ("eval/check_contract.py", "eval/check_contract.py"),
    ("eval/check_symbol_map.py", "eval/check_symbol_map.py"),
    ("docs/출력모양_합의안.md", "docs/출력모양_합의안.md"),
    ("docs/API_합의안.md", "docs/API_합의안.md"),
    ("docs/symbol_map_합의안.md", "docs/symbol_map_합의안.md"),
    ("docs/contracts/report.example.json", "docs/contracts/report.example.json"),
    ("docs/contracts/report_fail.example.json", "docs/contracts/report_fail.example.json"),
    ("docs/contracts/symbol_map.example.json", "docs/contracts/symbol_map.example.json"),
    ("docs/contracts/api_stub.py", "docs/contracts/api_stub.py"),
]

# 팀 구조에 맞게 바꿀 줄: (팀 저장소 안 위치, 원래 문자열, 바꿀 문자열)
PATCHES = [
    ("app.py", "    pip install streamlit\n    streamlit run app/streamlit_app.py",
     "    uv add streamlit\n    uv run streamlit run app.py"),
    ("app.py", "from backend import", "from src.ui.backend import"),
    ("app.py", "ROOT = Path(__file__).resolve().parent.parent", "ROOT = Path(__file__).resolve().parent"),
    ("src/ui/backend.py", "ROOT = Path(__file__).resolve().parent.parent", "ROOT = Path(__file__).resolve().parents[2]"),
    ("eval/run_system.py", 'sys.path.insert(0, str(HERE.parent / "app"))\nfrom backend import',
     'sys.path.insert(0, str(HERE.parent))\nfrom src.ui.backend import'),
    ("docs/contracts/api_stub.py", 'sys.path.insert(0, str(ROOT / "app"))\nfrom backend import',
     'sys.path.insert(0, str(ROOT))\nfrom src.ui.backend import'),
]

NEW = {
    "src/ui/__init__.py": '"""화면(app.py)이 쓰는 보조 코드 (4번 화면 · 평가)."""\n',
}


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    for src, dst in FILES:
        target = OUT / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / src, target)
    for dst, text in NEW.items():
        (OUT / dst).write_text(text, encoding="utf-8")
    for dst, old, new in PATCHES:
        path = OUT / dst
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise SystemExit(f"[바꿀 줄 없음] {dst}: {old!r} — 원본이 바뀌었으면 PATCHES 를 고치세요")
        path.write_text(text.replace(old, new), encoding="utf-8")
    shutil.copyfile(ROOT / "tools" / "team_copy_README.md", OUT / "docs" / "4번_화면평가_올리는법.md")
    print(f"완료: {OUT} ({len(FILES) + len(NEW) + 1}개 파일)")


if __name__ == "__main__":
    main()
