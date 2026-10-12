"""EVAL_RULES 2장 '성공 판정 기준'을 코드로 옮긴 공용 판정 모듈.

baseline(A)과 우리 시스템(B)을 같은 기준으로 판정하기 위해 둘 다 이 모듈을 사용한다.

    from verify import extract_code, judge
    code = extract_code(llm_response)
    result = judge(code, py="verify-env/Scripts/python.exe")
"""

import ast
import re
import subprocess

CODE_BLOCK = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


def extract_code(response: str) -> str:
    """0단계: 응답에서 첫 번째 ```python 코드 블록을 꺼낸다. 없으면 응답 전체."""
    m = CODE_BLOCK.search(response)
    return (m.group(1) if m else response).strip()


def import_lines(code: str) -> list[str]:
    tree = ast.parse(code)
    return [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]


def judge(code: str, py: str, timeout: int = 30) -> dict:
    """1~2단계 자동 판정 + 3단계(무효 변환) 의심 표시.

    3단계는 사람이 최종 확인한다. 여기서는 LangChain import 가 하나도 없으면
    suspect_invalid=True 로 표시만 한다.
    """
    r = {"success": False, "fail_stage": None, "error": None, "warning": False,
         "warning_messages": [], "uses_classic": False, "uses_community": False,
         "suspect_invalid": False, "invalid_transform": False}

    # 1단계: 문법 검사
    try:
        lines = import_lines(code)
    except SyntaxError as e:
        r.update(fail_stage="syntax", error=f"SyntaxError: {e.msg} (line {e.lineno})")
        return r

    langchain_lines = [l for l in lines if "langchain" in l or "langgraph" in l]
    r["uses_classic"] = any("langchain_classic" in l for l in lines)
    r["suspect_invalid"] = not code.strip() or not langchain_lines

    # 2단계: import 실행 (경고도 수집)
    try:
        p = subprocess.run([py, "-W", "always", "-c", "\n".join(lines)], capture_output=True,
                           text=True, timeout=timeout, encoding="utf-8")
    except subprocess.TimeoutExpired:
        r.update(fail_stage="timeout", error=f"Timeout ({timeout}s)")
        return r

    stderr = p.stderr.strip()
    if p.returncode != 0:
        r.update(fail_stage="import", error=(stderr.splitlines() or [""])[-1])
        return r

    # 예: langchain-community 는 import 만 해도 "sunset(지원 종료 중)" DeprecationWarning 을 낸다
    msgs = [l.split(": ", 1)[-1][:150] for l in stderr.splitlines() if "Warning" in l]
    r["warning"] = bool(msgs)
    r["warning_messages"] = sorted(set(msgs))
    r["uses_community"] = any("langchain_community" in l for l in lines)
    r["success"] = True
    return r
