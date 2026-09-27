"""فرآیند جدا برای یک دامنه MCP.

هر دامنه بستهٔ errors و logging_module خودش را دارد و نباید با بقیه
در یک مفسر پایتون وارد شود. این فرآیند یک خط JSON می‌خواند و یک خط
JSON می‌نویسد. لاگ روی stderr می‌ماند تا stdout فقط پروتکل باشد.
"""

from pathlib import Path
import importlib.util
import json
import sys
import traceback

from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    """دامنه را بالا می‌آورد و تا بسته‌شدن stdin درخواست را اجرا می‌کند."""
    protocol = sys.stdout
    sys.stdout = sys.stderr
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        protocol.write(_dump({"ok": False, "error_code": "WORKER_ERROR", "message": "نام دامنه لازم است"}) + "\n")
        return 1
    domain = args[0]
    load_error = None
    tools = {}
    try:
        tools = _load_tools(domain)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        load_error = f"دامنه {domain} بالا نیامد"

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        request_id = None
        try:
            message = json.loads(line)
            request_id = message.get("id")
            if load_error:
                reply = {
                    "ok": False,
                    "error_code": "DOMAIN_UNAVAILABLE",
                    "message": load_error,
                }
            else:
                reply = _handle(message, tools)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            reply = {
                "ok": False,
                "error_code": "WORKER_ERROR",
                "message": "اجرای درخواست در دامنه ناموفق بود",
            }
        reply["id"] = request_id
        protocol.write(_dump(reply) + "\n")
        protocol.flush()
    return 0


def _load_tools(domain: str) -> dict:
    _prepare_domain(domain)
    from mcp_server.server import mcp

    loaded = {}
    for tool in mcp._tool_manager.list_tools():
            annotations = tool.annotations
            read_only_hint = getattr(annotations, "read_only_hint", None)
            destructive_hint = getattr(annotations, "destructive_hint", None)
            read_only = (
                bool(read_only_hint)
                if read_only_hint is not None
                else tool.name.startswith(("list_", "get_"))
            )
            loaded[tool.name] = {
                "fn": tool.fn,
                "metadata": tool.fn_metadata,
                "is_async": tool.is_async,
                "catalog": {
                    "name": tool.name,
                    "title": tool.title,
                    "description": (tool.description or "").strip(),
                    "read_only": read_only,
                    "destructive": bool(destructive_hint),
                    "parameters": tool.parameters,
                },
            }
    return loaded


def _prepare_domain(domain: str) -> None:
    root = REPO_ROOT / domain
    paths_file = root / "paths.py"
    if paths_file.is_file():
        spec = importlib.util.spec_from_file_location(f"{domain}_paths", paths_file)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"paths دامنه {domain} خوانده نشد")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.ensure_import_path()
        return
    if domain != "crud":
        raise RuntimeError(f"دامنه {domain} مسیر import ندارد")
    ordered = [str(root), str(REPO_ROOT)]
    for path in ordered:
        if path in sys.path:
            sys.path.remove(path)
    for path in reversed(ordered):
        sys.path.insert(0, path)


def _handle(message: dict, tools: dict) -> dict:
    if message.get("op") == "catalog":
        return {
            "ok": True,
            "tools": [item["catalog"] for item in tools.values()],
        }
    name = message.get("tool")
    item = tools.get(name)
    if item is None:
        return {
            "ok": False,
            "error_code": "UNKNOWN_TOOL",
            "message": f"ابزار {name} در این دامنه نیست",
        }
    actor_id = message.get("actor_user_id")
    token = None
    if actor_id is not None:
        from auth.principal import reset_request_actor, set_request_actor

        token = set_request_actor(int(actor_id))
    try:
        if item["is_async"]:
            return {
                "ok": False,
                "error_code": "WORKER_ERROR",
                "message": "ابزار ناهمگام در API HTTP پشتیبانی نمی‌شود",
            }
        arguments = message.get("arguments") or {}
        try:
            validated = item["metadata"].validate_arguments(arguments)
        except ValidationError as exc:
            return {
                "ok": False,
                "error_code": "INVALID_INPUT",
                "message": str(exc)[:500],
            }
        result = item["fn"](**validated)
    finally:
        if token is not None:
            from auth.principal import reset_request_actor

            reset_request_actor(token)
    return {"ok": True, "result": result}


def _dump(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


if __name__ == "__main__":
    raise SystemExit(main())
