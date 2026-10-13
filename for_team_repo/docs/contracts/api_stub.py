"""연습용 가짜 API 서버 — docs/API_합의안.md 의 모양 그대로 응답한다.

1번은 실제 API를 만들 때 이 파일의 입력 · 출력 모양을 참고하고,
4번은 실제 API가 나오기 전에 화면과 평가의 연결을 이 서버로 미리 시험한다.
파이썬 기본 기능만 써서 따로 설치할 것이 없다.

실행:
    python docs/contracts/api_stub.py            # http://localhost:8000
    set MIGRATION_API_URL=http://localhost:8000  (PowerShell: $env:MIGRATION_API_URL="http://localhost:8000")
"""

import json
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.ui.backend import CONTRACT_VERSION, TARGET_VERSIONS, _mock, load_testset  # noqa: E402

TESTSET = load_testset()
INFO = {
    "contract_version": CONTRACT_VERSION,
    "target_versions": TARGET_VERSIONS,
    "model": "stub (가짜 응답)",
    "max_attempts": 3,
    "sandbox": {"python": "3.12", "langchain": "1.4.4", "langchain-core": "1.6.9"},
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _error(self, status: int, code: str, message: str):
        self._send(status, {"error": {"code": code, "message": message}})

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok"})
        elif self.path == "/info":
            self._send(200, INFO)
        else:
            self._error(404, "not_found", f"{self.path} 는 없는 주소입니다")

    def do_POST(self):
        if self.path != "/migrate":
            return self._error(404, "not_found", f"{self.path} 는 없는 주소입니다")
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except json.JSONDecodeError:
            return self._error(400, "invalid_json", "요청 본문이 JSON 이 아닙니다")
        code = body.get("code")
        if not isinstance(code, str) or not code.strip():
            return self._error(400, "empty_code", "code 에 변환할 코드를 넣어 주세요")
        if len(code) > 20000:
            return self._error(413, "code_too_long", "code 는 20000자 이하여야 합니다")
        target_version = body.get("target_version") or TARGET_VERSIONS[0]
        if target_version not in TARGET_VERSIONS:
            return self._error(400, "unsupported_version", f"target_version 은 {TARGET_VERSIONS} 중 하나여야 합니다")
        report = _mock(code, TESTSET, target_version)
        report.pop("mock", None)
        report.pop("example_id", None)
        report["request_id"] = body.get("request_id") or str(uuid.uuid4())
        self._send(200, report)

    def log_message(self, fmt, *args):
        print("[stub]", fmt % args)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"가짜 API 서버: http://localhost:{port}  (GET /health, GET /info, POST /migrate)")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
