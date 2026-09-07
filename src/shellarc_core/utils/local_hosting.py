import http.server
import socket
import threading
import time
import os
from pathlib import Path
from dotenv import load_dotenv

from pyngrok import ngrok

from shellarc_core.exception.user_exception import SA_LockConflictError
from shellarc_core.exception.structure_error import SA_AuthError, SA_ErrorCode

_is_hosting = False
_hosting_lock = threading.Lock()

def host_ngrok(html_content: str, 
               duration_minutes=5
               ) -> str:
    print("CKPT3")
    load_dotenv(verbose=True)
    project_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
    dotenv_path = project_ctx_dir / ".env"
    if not dotenv_path.exists():
        raise SA_AuthError(
            error_log=f"dotenv_path {dotenv_path} not exist",
            error_code=SA_ErrorCode.SA_9001
        )
    load_dotenv(dotenv_path)
    ngrok.set_auth_token(os.environ.get("Ngrok_authtoken"))
    global _is_hosting
    print("CKPT4")

    with _hosting_lock:
        if _is_hosting:
            raise SA_LockConflictError(
            error_log="lock conflict",
            frontend_msg="現在自動配信サービス使っている方がいますので、数分後またお試しください。\n" \
                "お急ぎの場合は管理権のある人をメンションしてください。"
            )
        _is_hosting = True

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    class HTMLHandler(http.server.BaseHTTPRequestHandler):

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))

        def log_message(self, format, *args):
            pass

    print("CKPT5")

    server = http.server.HTTPServer(("127.0.0.1", port), HTMLHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    tunnel = ngrok.connect(port)
    public_url = tunnel.public_url
    print("CKPT6")

    def auto_shutdown():
        global _is_hosting
        time.sleep(duration_minutes * 60)
        try:
            server.shutdown()
            server.server_close()
            ngrok.disconnect(public_url)
            ngrok.kill()
        finally:
            with _hosting_lock:
                _is_hosting = False

    shutdown_thread = threading.Thread(target=auto_shutdown)
    shutdown_thread.daemon = True
    shutdown_thread.start()

    return public_url

