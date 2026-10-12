"""실험 결과 JSON 으로 발표용 그래프(PNG)와 요약표를 만든다.

만드는 것 (charts/ 폴더):
  1_success_by_difficulty.png  시스템별 × 난이도별 성공률 (핵심 슬라이드)
  2_retry_effect.png           B 의 시도 횟수별 누적 성공률 (검증 루프 효과)
  3_success_quality.png        성공의 '질' 분해: 깔끔한 성공 / community 경고 / classic 의존 / 실패
  summary.md                   같은 숫자를 표로 (README·보고서에 붙여넣기용)

실행:
    pip install matplotlib
    python make_charts.py --a results/A_gpt-4o-mini_2026-10-14.json --b results/B_gpt-4o-mini_2026-10-15.json
    python make_charts.py --a ... --b ... --c results/C_cli.json      # langchain-cli 비교군이 있으면
"""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

HERE = Path(__file__).resolve().parent
DIFFS = ["easy", "medium", "hard"]
DIFF_LABEL = {"all": "전체", "easy": "쉬움", "medium": "중간", "hard": "어려움"}

# 색: 시스템마다 고정 (그래프가 바뀌어도 같은 시스템은 같은 색)
SYSTEM = {
    "B": ("우리 시스템", "#2a78d6"),
    "A": ("일반 LLM (baseline)", "#eb6834"),
    "C": ("langchain-cli", "#1baf7a"),
}
ORDER = ["B", "A", "C"]
# 성공의 질: 한 가지 파란색의 진하기(진할수록 좋음) + 실패는 회색
QUALITY = [
    ("clean", "깔끔한 성공", "#184f95"),
    ("community", "성공 (community 경고)", "#3987e5"),
    ("classic", "성공 (classic 의존)", "#86b6ef"),
    ("fail", "실패", "#d6d5cf"),
]
INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"


def korean_font():
    """설치된 한글 글꼴 하나를 고른다 (Windows: 맑은 고딕, Mac: AppleGothic)."""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"]:
        if name in installed:
            return name
    print("[경고] 한글 글꼴을 찾지 못했습니다. 글자가 깨지면 NanumGothic 을 설치하세요.")
    return "sans-serif"


def setup_style():
    plt.rcParams.update({
        "font.family": korean_font(),
        "axes.unicode_minus": False,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "font.size": 12, "axes.titlesize": 15, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.titlepad": 14,
    })


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else None


def rate(rows):
    return 100 * sum(r["success"] for r in rows) / len(rows) if rows else 0.0


def quality(r):
    if not r["success"] or r.get("invalid_transform"):
        return "fail"
    if r.get("uses_classic"):
        return "classic"
    if r.get("uses_community") or r.get("warning"):
        return "community"
    return "clean"


def chart_by_difficulty(data, out):
    groups = ["all"] + DIFFS
    systems = [s for s in ORDER if s in data]
    width = 0.8 / len(systems)
    fig, ax = plt.subplots(figsize=(10, 5.6))
    for i, s in enumerate(systems):
        rows = data[s]
        vals = [rate(rows if g == "all" else [r for r in rows if r["difficulty"] == g]) for g in groups]
        xs = [g + (i - (len(systems) - 1) / 2) * width for g in range(len(groups))]
        name, color = SYSTEM[s]
        bars = ax.bar(xs, vals, width * 0.92, color=color, label=name, zorder=3,
                      edgecolor=SURFACE, linewidth=2)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.0f}%", ha="center",
                    va="bottom", fontsize=11, color=INK2)
    ax.set_xticks(range(len(groups)), [DIFF_LABEL[g] for g in groups])
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20), [f"{v}%" for v in range(0, 101, 20)])
    ax.set_ylabel("import 성공률")
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", length=0)
    ax.set_title("난이도별 import 성공률")
    ax.legend(frameon=False, loc="upper right", ncol=len(systems), bbox_to_anchor=(1, 1.1))
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def chart_retry(data, out, max_attempts):
    b = data["B"]
    n = len(b)
    ks = list(range(1, max_attempts + 1))
    cum = [100 * sum(r["success"] and r["attempts"] <= k for r in b) / n for k in ks]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    name, color = SYSTEM["B"]
    ax.plot(ks, cum, color=color, linewidth=2.5, marker="o", markersize=9, zorder=3,
            markeredgecolor=SURFACE, markeredgewidth=2)
    for k, v in zip(ks, cum):
        ax.text(k, v + 3, f"{v:.0f}%", ha="center", va="bottom", fontsize=12, color=INK)
    if "A" in data:
        a = rate(data["A"])
        a_name, a_color = SYSTEM["A"]
        ax.axhline(a, color=a_color, linewidth=2, linestyle=(0, (5, 4)), zorder=2)
        ax.text(0.75, a + 2, f"{a_name} {a:.0f}%", va="bottom", ha="left", fontsize=11, color=INK2)
    gain = cum[-1] - cum[0]
    ax.annotate(f"검증 루프 효과 +{gain:.0f}%p", xy=(ks[-1] - 0.03, cum[-1] + 1),
                xytext=(ks[-1] - 0.45, min(cum[-1] + 14, 106)), ha="right", va="center",
                fontsize=12, fontweight="bold", color=INK,
                arrowprops=dict(arrowstyle="->", color=MUTED, linewidth=1.2))
    ax.set_xticks(ks, [f"{k}회" for k in ks])
    ax.set_xlim(0.7, max_attempts + 0.7)
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20), [f"{v}%" for v in range(0, 101, 20)])
    ax.set_xlabel("시도 횟수 (실패하면 재검색 후 다시 변환)")
    ax.set_ylabel("누적 성공률")
    ax.grid(axis="x", visible=False)
    ax.set_title(f"{name}: 시도 횟수별 누적 성공률")
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def chart_quality(data, out):
    systems = [s for s in ORDER if s in data][::-1]  # 위에서부터 B, A, C
    fig, ax = plt.subplots(figsize=(10, 1.6 + 1.0 * len(systems)))
    for y, s in enumerate(systems):
        rows = data[s]
        left = 0
        for key, label, color in QUALITY:
            v = 100 * sum(quality(r) == key for r in rows) / len(rows)
            if v == 0:
                continue
            ax.barh(y, v, left=left, height=0.6, color=color, edgecolor=SURFACE, linewidth=2, zorder=3)
            if v >= 7:
                txt = "white" if key in ("clean", "community") else INK
                ax.text(left + v / 2, y, f"{v:.0f}%", ha="center", va="center", fontsize=11, color=txt)
            left += v
    ax.set_yticks(range(len(systems)), [SYSTEM[s][0] for s in systems])
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 25), [f"{v}%" for v in range(0, 101, 25)])
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_title("성공의 질: 지금 통과해도 곧 깨질 수 있는 코드")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in QUALITY]
    ax.legend(handles, [l for _, l, _ in QUALITY], frameon=False, ncol=4, loc="upper left",
              bbox_to_anchor=(0, -0.18 if len(systems) > 1 else -0.35), fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)


def summary_table(data, out):
    lines = ["| 시스템 | 전체 | 쉬움 | 중간 | 어려움 | 깔끔한 성공 | community 경고 | classic 의존 | 평균 시도 |",
             "|---|---|---|---|---|---|---|---|---|"]
    for s in [s for s in ORDER if s in data]:
        rows = data[s]
        by = [rate([r for r in rows if r["difficulty"] == d]) for d in DIFFS]
        q = {k: 100 * sum(quality(r) == k for r in rows) / len(rows) for k, _, _ in QUALITY}
        ok = [r for r in rows if r["success"]]
        avg = sum(r.get("attempts", 1) for r in ok) / len(ok) if ok else 0
        lines.append(f"| {SYSTEM[s][0]} | {rate(rows):.1f}% | " + " | ".join(f"{v:.1f}%" for v in by)
                     + f" | {q['clean']:.1f}% | {q['community']:.1f}% | {q['classic']:.1f}% | {avg:.2f} |")
    if "B" in data:
        b = data["B"]
        first = 100 * sum(r.get("first_try_success", False) for r in b) / len(b)
        lines += ["", f"- 우리 시스템 1회차 성공률: {first:.1f}%",
                  f"- 우리 시스템 최종 성공률: {rate(b):.1f}%",
                  f"- **검증 루프 효과: +{rate(b) - first:.1f}%p**"]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="실험 결과 그래프 만들기")
    ap.add_argument("--a", help="baseline(A) 결과 JSON")
    ap.add_argument("--b", help="우리 시스템(B) 결과 JSON")
    ap.add_argument("--c", help="langchain-cli(C) 결과 JSON (선택)")
    ap.add_argument("--max-attempts", type=int, default=3, help="EVAL_RULES 5장 최대 시도 횟수")
    ap.add_argument("--out", default=str(HERE / "charts"))
    a = ap.parse_args()

    data = {k: v for k, v in {"A": load(a.a), "B": load(a.b), "C": load(a.c)}.items() if v}
    if not data:
        ap.error("--a, --b, --c 중 하나 이상 필요합니다")

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    setup_style()

    chart_by_difficulty(data, out / "1_success_by_difficulty.png")
    if "B" in data:
        chart_retry(data, out / "2_retry_effect.png", a.max_attempts)
    chart_quality(data, out / "3_success_quality.png")
    print(summary_table(data, out / "summary.md"))
    print(f"\n그래프 저장 위치: {out}")


if __name__ == "__main__":
    main()
