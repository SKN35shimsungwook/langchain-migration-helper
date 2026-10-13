"""baseline(A) 실험: 일반 LLM 에 '최신 버전으로 바꿔줘'만 요청하고 결과를 판정한다.

EVAL_RULES 5-1 의 프롬프트를 그대로 사용한다. (문서나 힌트는 주지 않음)
판정은 verify.py (B 와 같은 기준) 로 한다.

준비:
    pip install openai
    OpenAI API 키를 환경 변수 OPENAI_API_KEY 에 넣어 둔다.

실행:
    python run_baseline.py --py verify-env/Scripts/python.exe --model gpt-4o-mini
    python run_baseline.py --py verify-env/Scripts/python.exe --limit 3     # 3개만 먼저 시험
    python run_baseline.py --py verify-env/Scripts/python.exe --mock        # API 호출 없이 흐름만 확인

중간에 멈춰도 다시 실행하면 이미 끝난 항목은 건너뛴다. (같은 날짜·모델 결과 파일 기준)
"""

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from verify import extract_code, judge

HERE = Path(__file__).resolve().parent

# EVAL_RULES 5-1 baseline 프롬프트 (수정 금지)
BASELINE_PROMPT = """다음 Python 코드는 구버전 LangChain으로 작성되었습니다.
LangChain 1.x 최신 버전에서 동작하도록 코드를 변환해 주세요.
변환된 전체 코드를 ```python 코드 블록 하나로 출력해 주세요.

{old_code}"""


def ask_llm(client, model: str, old_code: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[{"role": "user", "content": BASELINE_PROMPT.format(old_code=old_code)}],
    )
    return resp.choices[0].message.content or ""


def mock_llm(item: dict) -> str:
    """--mock: API 없이 흐름 확인용. 정답 방향 import 만 담은 응답을 흉내 낸다."""
    return f"변환한 코드입니다.\n```python\n{item['target_imports']}\n```"


def summarize(results: list[dict]) -> None:
    by = defaultdict(lambda: [0, 0])
    for r in results:
        by[r["difficulty"]][0] += r["success"]
        by[r["difficulty"]][1] += 1
    ok = [r for r in results if r["success"]]
    n = len(results)

    def pct(a, b):
        return f"{a / b * 100:.1f}%" if b else "-"

    print("\n=== baseline(A) 결과 ===")
    print(f"전체 성공률: {len(ok)}/{n} = {pct(len(ok), n)}")
    for d in ["easy", "medium", "hard"]:
        s, t = by[d]
        print(f"  {d:<6}: {s}/{t} = {pct(s, t)}")
    print(f"경고 비율 (성공 중):        {pct(sum(r['warning'] for r in ok), len(ok))}")
    print(f"classic 의존 비율 (성공 중): {pct(sum(r['uses_classic'] for r in ok), len(ok))}")
    print(f"community 사용 비율 (성공 중): {pct(sum(r['uses_community'] for r in ok), len(ok))}"
          "  ← langchain-community 는 지원 종료 중")
    suspects = [r["id"] for r in results if r["suspect_invalid"]]
    if suspects:
        print(f"[확인 필요] 무효 변환 의심: {suspects}  → 직접 보고 invalid_transform 을 표시하세요")
    stages = defaultdict(int)
    for r in results:
        if not r["success"]:
            stages[r["fail_stage"]] += 1
    if stages:
        print("실패 단계: " + ", ".join(f"{k} {v}" for k, v in stages.items()))


def main():
    ap = argparse.ArgumentParser(description="baseline(A) 실험")
    ap.add_argument("--py", required=True, help="검증 환경의 python 경로")
    ap.add_argument("--model", default="gpt-4o-mini", help="비교에 쓸 모델 (B와 같아야 함)")
    ap.add_argument("--testset", default=str(HERE / "testset.json"))
    ap.add_argument("--limit", type=int, help="앞에서부터 N개만 실행")
    ap.add_argument("--mock", action="store_true", help="API 호출 없이 흐름만 확인")
    a = ap.parse_args()

    items = json.loads(Path(a.testset).read_text(encoding="utf-8"))
    if a.limit:
        items = items[: a.limit]

    tag = "mock" if a.mock else a.model
    out = HERE / "results" / f"A_{tag}_{date.today()}.json"
    out.parent.mkdir(exist_ok=True)
    results = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
    done = {r["id"] for r in results}

    client = None
    if not a.mock:
        from openai import OpenAI
        client = OpenAI()  # OPENAI_API_KEY 환경 변수 사용

    for i, item in enumerate(items, 1):
        if item["id"] in done:
            continue
        print(f"[{i}/{len(items)}] {item['id']} ...", end=" ", flush=True)
        response = mock_llm(item) if a.mock else ask_llm(client, a.model, item["old_code"])
        code = extract_code(response)
        v = judge(code, a.py)
        results.append({
            "id": item["id"], "difficulty": item["difficulty"], "system": "A", "model": tag,
            "attempts": 1, "first_try_success": v["success"], **v,
            "migrated_code": code, "raw_response": response,
        })
        # 한 항목마다 저장 → 중간에 멈춰도 결과가 남는다
        out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print("성공" if v["success"] else f"실패 ({v['fail_stage']}: {v['error'][:60]})")

    print(f"\n결과 파일: {out}")
    summarize(results)


if __name__ == "__main__":
    main()
