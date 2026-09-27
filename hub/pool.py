"""صف درخواست به فرآیندهای دامنه.

هر دامنه یک فرآیند و یک قفل دارد. درخواست‌های همان دامنه پشت‌سرهم
اجرا می‌شوند تا بازیگر درخواست قاطی نشود.
"""

from subprocess import PIPE, Popen, TimeoutExpired
import json
import sys
import threading

from hub.bootstrap import REPO_ROOT

from auth.http import DOMAIN_UNAVAILABLE


class WorkerError(Exception):
    """دامنه جواب قابل‌استفاده نداد."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class DomainPool:
    """فرآیندهای دامنه را نگه می‌دارد و ابزار را صدا می‌زند."""

    def __init__(self, domains: tuple, timeout_seconds: int) -> None:
        self._timeout = timeout_seconds
        self._workers = {
            name: _Worker(name, timeout_seconds) for name in domains
        }

    def start(self) -> None:
        for worker in self._workers.values():
            worker.start()

    def stop(self) -> None:
        for worker in self._workers.values():
            worker.stop()

    def status(self) -> list:
        return [worker.status() for worker in self._workers.values()]

    def catalog(self) -> list:
        groups = []
        for worker in self._workers.values():
            groups.append({
                "domain": worker.domain,
                "ready": worker.ready,
                "message": worker.error,
                "tools": worker.tools,
            })
        return groups

    def tool_info(self, domain: str, tool: str):
        worker = self._workers.get(domain)
        if worker is None:
            return None
        for item in worker.tools:
            if item.get("name") == tool:
                return item
        return None

    def call(self, domain: str, tool: str, arguments: dict, actor_user_id: int) -> dict:
        worker = self._workers.get(domain)
        if worker is None or not worker.ready:
            raise WorkerError(DOMAIN_UNAVAILABLE, f"دامنه {domain} در دسترس نیست")
        try:
            reply = self._request_call(worker, tool, arguments, actor_user_id)
        except WorkerError as exc:
            if exc.error_code != DOMAIN_UNAVAILABLE:
                raise
            worker.start()
            if not worker.ready:
                raise WorkerError(DOMAIN_UNAVAILABLE, worker.error or exc.message) from exc
            reply = self._request_call(worker, tool, arguments, actor_user_id)
        if not reply.get("ok"):
            raise WorkerError(
                str(reply.get("error_code") or DOMAIN_UNAVAILABLE),
                str(reply.get("message") or "اجرای ابزار ناموفق بود"),
            )
        result = reply.get("result")
        if not isinstance(result, dict):
            return {"status": "success", "result": result}
        return result

    def _request_call(self, worker, tool: str, arguments: dict, actor_user_id: int) -> dict:
        return worker.request({
            "op": "call",
            "tool": tool,
            "arguments": arguments,
            "actor_user_id": actor_user_id,
        })


class _Worker:
    def __init__(self, domain: str, timeout_seconds: int) -> None:
        self.domain = domain
        self._timeout = timeout_seconds
        self._process = None
        self._lock = threading.Lock()
        self._seq = 0
        self.ready = False
        self.error = None
        self.tools = []

    def start(self) -> None:
        try:
            self._spawn()
            reply = self.request({"op": "catalog"})
        except WorkerError as exc:
            self.ready = False
            self.error = exc.message
            self.tools = []
            return
        if not reply.get("ok"):
            self.ready = False
            self.error = str(reply.get("message") or "کاتالوگ دامنه خوانده نشد")
            self.tools = []
            return
        self.tools = list(reply.get("tools") or [])
        self.ready = True
        self.error = None

    def stop(self) -> None:
        process = self._process
        self._process = None
        self.ready = False
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for stream in (process.stdin, process.stdout):
            if stream is not None and not stream.closed:
                stream.close()

    def status(self) -> dict:
        return {
            "domain": self.domain,
            "ready": self.ready,
            "tools": len(self.tools),
            "message": self.error,
        }

    def request(self, message: dict) -> dict:
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None:
                raise WorkerError(DOMAIN_UNAVAILABLE, f"فرآیند دامنه {self.domain} بسته است")
            self._seq += 1
            message = dict(message)
            message["id"] = self._seq
            payload = json.dumps(message, ensure_ascii=False) + "\n"
            try:
                process.stdin.write(payload)
                process.stdin.flush()
            except BrokenPipeError as exc:
                self.ready = False
                raise WorkerError(DOMAIN_UNAVAILABLE, f"دامنه {self.domain} قطع شد") from exc
            line = self._read_line(process)
            if not line:
                self.ready = False
                raise WorkerError(DOMAIN_UNAVAILABLE, f"دامنه {self.domain} بدون پاسخ بسته شد")
            try:
                reply = json.loads(line)
            except json.JSONDecodeError as exc:
                self.ready = False
                raise WorkerError(DOMAIN_UNAVAILABLE, f"پاسخ دامنه {self.domain} نامعتبر بود") from exc
            if reply.get("id") != self._seq:
                self.ready = False
                raise WorkerError(DOMAIN_UNAVAILABLE, f"پاسخ دامنه {self.domain} با درخواست جور نبود")
            return reply

    def _spawn(self) -> None:
        self.stop()
        self._process = Popen(
            [sys.executable, "-m", "hub.worker", self.domain],
            cwd=str(REPO_ROOT),
            stdin=PIPE,
            stdout=PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

    def _read_line(self, process) -> str:
        box = {}

        def _read() -> None:
            box["line"] = process.stdout.readline()

        thread = threading.Thread(target=_read, daemon=True)
        thread.start()
        thread.join(self._timeout)
        if thread.is_alive():
            self.stop()
            raise WorkerError(DOMAIN_UNAVAILABLE, f"دامنه {self.domain} در مهلت مقرر جواب نداد")
        return box.get("line") or ""
