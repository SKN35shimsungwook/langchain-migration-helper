"""EVAL_RULES 2장 '성공 판정 기준'을 코드로 옮긴 공용 판정 모듈.

baseline(A)과 우리 시스템(B)을 같은 기준으로 판정하기 위해 둘 다 이 모듈을 사용한다.
3번의 verifier (b) '샌드박스 import · 속성 검증'도 이 모듈을 출발점으로 쓴다.

    from verify import extract_code, judge
    code = extract_code(llm_response)
    result = judge(code, py="verify-env/Scripts/python.exe")
"""

import ast
import json
import re
import subprocess

CODE_BLOCK = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)
ATTR_FAIL = "ATTRIBUTE_MISSING:"


def extract_code(response: str) -> str:
    """0단계: 응답에서 첫 번째 ```python 코드 블록을 꺼낸다. 없으면 응답 전체."""
    m = CODE_BLOCK.search(response)
    return (m.group(1) if m else response).strip()


def import_lines(code: str) -> list[str]:
    tree = ast.parse(code)
    return [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]


def imported_names(code: str) -> set[str]:
    """import 로 코드에 들어온 이름 (예: ChatOpenAI, hub, langchain_core)."""
    names = set()
    for n in ast.walk(ast.parse(code)):
        if isinstance(n, ast.Import):
            names |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            names |= {a.asname or a.name for a in n.names if a.name != "*"}
    return names


def attribute_chains(code: str) -> list[str]:
    """import 한 이름에서 바로 이어지는 속성 접근 (예: PromptTemplate.from_template, hub.pull).

    인스턴스 속성(llm.invoke 처럼 변수에 담은 뒤 쓰는 것)은 실행 전에는 알 수 없으므로 검사하지 않는다.
    """
    roots = imported_names(code)
    chains = set()
    for n in ast.walk(ast.parse(code)):
        if not isinstance(n, ast.Attribute):
            continue
        parts, cur = [], n
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name) and cur.id in roots:
            chains.add(".".join([cur.id] + parts[::-1]))
    # 긴 사슬이 짧은 사슬을 포함하므로 가장 긴 것만 남긴다
    return sorted(c for c in chains if not any(o != c and o.startswith(c + ".") for o in chains))


def _check_script(lines: list[str], chains: list[str]) -> str:
    # 'import langchain_core' 뒤 'langchain_core.prompts' 처럼 아직 안 불러온 하위 모듈은
    # 한 번 불러온 뒤 다시 확인해서 잘못된 실패를 막는다
    return "\n".join(lines + [
        "import sys as _s, importlib as _il",
        "def _ok(_c):",
        "    try:",
        "        eval(_c); return True",
        "    except AttributeError:",
        "        pass",
        "    _p = _c.split('.')",
        "    for _i in range(2, len(_p) + 1):",
        "        try:",
        "            _il.import_module('.'.join(_p[:_i]))",
        "        except Exception:",
        "            break",
        "    try:",
        "        eval(_c); return True",
        "    except Exception:",
        "        return False",
        "_missing = []",
        f"for _c in {json.dumps(chains, ensure_ascii=False)}:",
        "    if not _ok(_c):",
        "        _missing.append(_c)",
        "if _missing:",
        f"    print({ATTR_FAIL!r} + ', '.join(_missing), file=_s.stderr)",
        "    _s.exit(3)",
    ])


def judge(code: str, py: str, timeout: int = 30) -> dict:
    """1~2단계 자동 판정 + 3단계(무효 변환) 의심 표시.

    2단계는 (a) import 실행 (b) import 한 이름의 속성 접근 확인 두 가지다.
    3단계는 사람이 최종 확인한다. 여기서는 LangChain import 가 하나도 없으면
    suspect_invalid=True 로 표시만 한다.
    """
    r = {"success": False, "fail_stage": None, "error": None, "warning": False,
         "warning_messages": [], "uses_classic": False, "uses_community": False,
         "checked_attributes": [], "suspect_invalid": False, "invalid_transform": False}

    # 1단계: 문법 검사
    try:
        lines = import_lines(code)
        chains = attribute_chains(code)
    except SyntaxError as e:
        r.update(fail_stage="syntax", error=f"SyntaxError: {e.msg} (line {e.lineno})")
        return r

    langchain_lines = [l for l in lines if "langchain" in l or "langgraph" in l]
    r["uses_classic"] = any("langchain_classic" in l for l in lines)
    r["suspect_invalid"] = not code.strip() or not langchain_lines
    r["checked_attributes"] = chains

    # 2단계: import 실행 + 속성 확인 (경고도 수집)
    try:
        p = subprocess.run([py, "-W", "always", "-c", _check_script(lines, chains)], capture_output=True,
                           text=True, timeout=timeout, encoding="utf-8")
    except subprocess.TimeoutExpired:
        r.update(fail_stage="timeout", error=f"Timeout ({timeout}s)")
        return r

    stderr = p.stderr.strip()
    if p.returncode != 0:
        last = (stderr.splitlines() or [""])[-1]
        if last.startswith(ATTR_FAIL):
            r.update(fail_stage="attribute", error="속성 없음: " + last[len(ATTR_FAIL):])
        else:
            r.update(fail_stage="import", error=last)
        return r

    # 예: langchain-community 는 import 만 해도 "sunset(지원 종료 중)" DeprecationWarning 을 낸다
    msgs = [l.split(": ", 1)[-1][:150] for l in stderr.splitlines() if "Warning" in l]
    r["warning"] = bool(msgs)
    r["warning_messages"] = sorted(set(msgs))
    r["uses_community"] = any("langchain_community" in l for l in lines)
    r["success"] = True
    return r
