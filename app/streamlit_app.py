"""LangChain 마이그레이션 도우미 화면 (4번 담당).

실행:
    pip install streamlit
    streamlit run app/streamlit_app.py

탭 두 개:
  변환하기   코드 입력 → 진행 단계 → 결과, 바뀐 줄 비교, 근거 링크, 검증 배지
  성능 비교  eval/charts 의 그래프와 요약표 (make_charts.py 결과)
"""

import difflib
from pathlib import Path

import streamlit as st

from backend import load_testset, migrate

ROOT = Path(__file__).resolve().parent.parent
CHARTS = ROOT / "eval" / "charts"
DIFF_LABEL = {"easy": "쉬움", "medium": "중간", "hard": "어려움"}

st.set_page_config(page_title="LangChain 마이그레이션 도우미", page_icon=":material/sync_alt:", layout="wide")


@st.cache_data
def testset() -> list[dict]:
    return load_testset()


examples = testset()

st.title("LangChain 마이그레이션 도우미")
st.caption("구버전 LangChain 코드를 최신 버전으로 바꾸고, 문서 근거와 실행 근거로 확인합니다.")

convert_tab, compare_tab = st.tabs([":material/sync_alt: 변환하기", ":material/bar_chart: 성능 비교"])

with convert_tab:
    labels = {f"{e['id']} · {DIFF_LABEL[e['difficulty']]} · {e['why_broken'][:28]}": e for e in examples}
    choice = st.selectbox("예제 불러오기", ["직접 입력"] + list(labels), key="example")
    default = labels[choice]["old_code"] if choice in labels else ""
    with st.form("convert"):
        code = st.text_area("구버전 코드", value=default, height=220, key=f"code_{choice}")
        submitted = st.form_submit_button("변환하기", icon=":material/play_arrow:", type="primary")

    if submitted and code.strip():
        report = migrate(code, examples)
        st.session_state["report"] = report

    report = st.session_state.get("report")
    if report:
        if report.get("mock"):
            st.info("지금은 가짜 응답(mock)입니다. 백엔드 API가 연결되면 실제 파이프라인 결과가 표시됩니다.",
                    icon=":material/science:")

        # 진행 단계 (파이프라인 ①~⑤와 되돌아가기)
        ok = report["verification"]["success"]
        with st.status("파이프라인 진행 기록", state="complete" if ok else "error", expanded=False):
            st.write("① analyzer · 심볼 추출")
            st.write("② retriever · symbol_map 조회 + 문서 검색")
            st.write("③ rewriter · 근거 ID를 붙여 코드 재작성")
            for a in report["attempt_log"]:
                if a["fail_stage"]:
                    st.write(f"④ verifier · {a['attempt']}회차 실패 ({a['error_type']}: {a['target']}) → ②로 돌아가 다시 찾기")
                else:
                    st.write(f"④ verifier · {a['attempt']}회차 통과")
            st.write("⑤ report · 결과 정리")

        with st.container(horizontal=True):
            if ok:
                st.badge(f"검증 통과 · {report['attempts']}회 시도", icon=":material/check_circle:", color="green")
            else:
                st.badge("검증 실패", icon=":material/error:", color="red")
            evidence = report["changes"]
            if evidence:
                valid = sum(c["evidence_ok"] for c in evidence)
                st.badge(f"근거 확인 {valid}/{len(evidence)}", icon=":material/menu_book:", color="blue")

        if not ok:
            st.error(report["verification"]["error"] or "변환에 실패했습니다.")
        else:
            left, right = st.columns(2)
            with left:
                st.subheader("변경 전", divider="gray")
                st.code(report["original_code"], language="python")
            with right:
                st.subheader("변경 후", divider="blue")
                st.code(report["migrated_code"], language="python")

            st.subheader("바뀐 줄", divider="gray")
            diff = difflib.unified_diff(report["original_code"].splitlines(), report["migrated_code"].splitlines(),
                                        "변경 전", "변경 후", lineterm="")
            st.code("\n".join(diff), language="diff")

            st.subheader("변경표와 근거", divider="gray")
            st.dataframe(
                report["changes"], hide_index=True,
                column_order=["old", "new", "reason", "evidence_url", "evidence_ok"],
                column_config={
                    "old": st.column_config.TextColumn("구"),
                    "new": st.column_config.TextColumn("신"),
                    "reason": st.column_config.TextColumn("이유"),
                    "evidence_url": st.column_config.LinkColumn("근거 문서", display_text="문서 열기"),
                    "evidence_ok": st.column_config.CheckboxColumn("근거 확인"),
                },
            )

with compare_tab:
    summary = CHARTS / "summary.md"
    pictures = [("난이도별 성공률", "1_success_by_difficulty.png"),
                ("검증 루프 효과", "2_retry_effect.png"),
                ("성공의 질", "3_success_quality.png")]
    if summary.exists():
        st.markdown(summary.read_text(encoding="utf-8"))
        for title, name in pictures:
            if (CHARTS / name).exists():
                st.subheader(title, divider="gray")
                st.image(str(CHARTS / name))
    else:
        st.info("아직 실험 전입니다. 실험 후 eval 폴더에서 make_charts.py 를 실행하면 이곳에 그래프와 요약표가 나타납니다.",
                icon=":material/hourglass_empty:")
        st.code("python make_charts.py --a results/A_[모델]_[날짜].json --b results/B_[모델]_[날짜].json",
                language="bash")
