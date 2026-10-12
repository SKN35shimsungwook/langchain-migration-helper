"""slides/*.html (claude.ai 슬라이드 원본)을 브라우저에서 보는 발표자료.html 한 파일로 합친다.

실행:
    python build_slides.py

PDF 만들기 (Windows, Edge):
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --headless=new --no-pdf-header-footer
        --virtual-time-budget=10000 --print-to-pdf=발표자료.pdf 발표자료.html
    (한글 경로가 안 되면 영문 경로로 복사한 뒤 실행)
"""

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "발표자료.html"
STATUS = "초안 · [__] 표시는 실험 결과가 나오면 채웁니다"

CONNECTOR = re.compile(r"<x-connector([^>]*)></x-connector>")
ATTR = re.compile(r'([\w-]+)="([^"]*)"')


def connector_svg(attrs: str, idx: int) -> str:
    """x-connector(슬라이드 전용 태그)를 일반 SVG 선으로 바꾼다."""
    a = dict(ATTR.findall(attrs))
    style = dict(kv.split(":", 1) for kv in a.get("style", "").split(";") if ":" in kv)
    color = style.get("color", "#8A8F98").strip()
    width = style.get("border-width", "2px").strip().replace("px", "")
    dash = ' stroke-dasharray="10 8"' if "dashed" in style.get("border-style", "") else ""
    x1, y1, x2, y2 = (float(a[k]) for k in ("x1", "y1", "x2", "y2"))
    route = a.get("route", "straight")
    if route == "vh":
        pts = [(x1, y1), (x1, y2), (x2, y2)]
    elif route == "hv":
        pts = [(x1, y1), (x2, y1), (x2, y2)]
    else:
        pts = [(x1, y1), (x2, y2)]
    points = " ".join(f"{x:g},{y:g}" for x, y in pts)
    head = a.get("head", "end")
    marker = ""
    if head in ("end", "both"):
        marker = (f'<defs><marker id="h{idx}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" '
                  f'markerHeight="4" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>')
    end = f' marker-end="url(#h{idx})"' if marker else ""
    return (f'<svg class="conn" viewBox="0 0 1920 1080" aria-hidden="true">{marker}'
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="{width}"{dash}{end}/></svg>')


def build():
    deck = json.loads((HERE / "deck.json").read_text(encoding="utf-8"))
    font_href = next(iter(deck["faces"].values()))["href"]
    blocks, n = [], 0
    for i, sid in enumerate(deck["order"], 1):
        src = (HERE / "slides" / f"{sid}.html").read_text(encoding="utf-8")
        m = re.search(r"<aside>(.*?)</aside>", src, re.S)
        notes = m.group(1).strip() if m else ""
        src = re.sub(r"<aside>.*?</aside>\s*", "", src, flags=re.S)

        def repl(mm):
            nonlocal n
            n += 1
            return connector_svg(mm.group(1), n)

        src = CONNECTOR.sub(repl, src).strip()
        note_html = (f'<details class="notes"><summary>발표자 노트</summary><p>{html.escape(notes)}</p></details>'
                     if notes else "")
        blocks.append(f'<figure class="slide" id="slide-{i}" aria-label="{i}번 슬라이드">'
                      f'<div class="frame">{src}</div><figcaption>{i} / {len(deck["order"])}</figcaption>{note_html}</figure>')

    page = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(deck["title"])}</title>
<link rel="stylesheet" href="{font_href}">
<style>
:root {{ --bg: #E9ECEF; --ink: #18202B; --ink-2: #4A5565; --badge: #8A4B12; --badge-bg: #FBEBD8; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg: #101419; --ink: #E9EDF2; --ink-2: #A9B3C1; --badge: #F3B67C; --badge-bg: #3A2614; color-scheme: dark; }} }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: 'IBM Plex Sans KR', 'Malgun Gothic', sans-serif; padding: 32px 16px 64px; }}
header.top, main {{ max-width: 1100px; margin: 0 auto; }}
header.top {{ display: flex; flex-direction: column; gap: 8px; padding-bottom: 24px; }}
header.top h1 {{ margin: 0; font-size: clamp(1.6rem, 4vw, 2.2rem); }}
header.top p {{ margin: 0; color: var(--ink-2); line-height: 1.6; }}
.badge {{ align-self: flex-start; font-size: 13px; font-weight: 700; color: var(--badge); background: var(--badge-bg); border-radius: 999px; padding: 2px 10px; }}
main {{ display: flex; flex-direction: column; gap: 40px; }}
figure.slide {{ margin: 0; display: flex; flex-direction: column; gap: 8px; }}
.frame {{ word-break: keep-all; overflow-wrap: break-word; position: relative; width: 100%; aspect-ratio: 16 / 9; overflow: hidden; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,.18); }}
.frame > section {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: hidden; transform: scale(var(--s, .5)); transform-origin: 0 0; }}
.frame h1, .frame h2, .frame h3, .frame p, .frame ul, .frame ol {{ margin: 0; }}
.frame h1, .frame h2, .frame h3 {{ font-weight: 600; }}
.frame hr {{ margin: 0; border: none; width: 100%; }}
.frame table {{ width: 100%; border-collapse: separate; border-spacing: 0; overflow: hidden; }}
.frame th, .frame td {{ padding: .35em .6em; text-align: left; vertical-align: top; border-bottom: 1px solid #E1E0D9; }}
.frame th {{ font-weight: 600; }}
.frame tr:last-child td {{ border-bottom: none; }}
.frame svg.conn {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; pointer-events: none; }}
figcaption {{ font-size: 13px; color: var(--ink-2); text-align: right; }}
details.notes {{ font-size: 15px; line-height: 1.7; color: var(--ink-2); }}
details.notes summary {{ cursor: pointer; font-weight: 700; }}
details.notes p {{ margin: 6px 0 0; }}
@page {{ size: 1920px 1080px; margin: 0; }}
@media print {{
  body {{ padding: 0; background: #FFFFFF; }}
  header.top, figcaption, details.notes {{ display: none; }}
  main {{ max-width: none; gap: 0; }}
  .frame {{ width: 1920px; height: 1080px; aspect-ratio: auto; border-radius: 0; box-shadow: none; break-after: page; }}
  .frame > section {{ transform: none !important; }}
}}
</style>
</head>
<body>
<header class="top">
  <span class="badge">{STATUS}</span>
  <h1>{html.escape(deck["title"])}</h1>
  <p>슬라이드 {len(deck["order"])}장 · 각 슬라이드 아래 "발표자 노트"를 누르면 발표 대본이 보입니다 ·
  <a href="발표자료.pdf">PDF로 보기</a> · <a href="../index.html">안내서 모음으로</a></p>
</header>
<main>
{chr(10).join(blocks)}
</main>
<script>
function fit() {{ document.querySelectorAll('.frame').forEach(f => f.style.setProperty('--s', f.clientWidth / 1920)); }}
fit();
if ('ResizeObserver' in window) {{ new ResizeObserver(fit).observe(document.querySelector('main')); }} else {{ addEventListener('resize', fit); }}
</script>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"{OUT.name}: 슬라이드 {len(blocks)}장, 연결선 {n}개 변환")


if __name__ == "__main__":
    build()
