"""شرح OpenAPI برای کلاینت وب و موبایل."""

from hub.registry import DASHBOARD_ROUTES


def build_openapi(catalog: list) -> dict:
    """کاتالوگ دامنه‌ها را به سند OpenAPI 3 تبدیل می‌کند."""
    paths = {
        "/api/v1/health": _path("get", "سلامت سرویس", auth=False),
        "/api/v1/catalog": _path("get", "فهرست دامنه‌ها و ابزارها", auth=False),
        "/api/v1/openapi.json": _path("get", "همین سند", auth=False),
        "/api/v1/auth/login": {
            "post": _operation(
                "ورود و دریافت توکن",
                auth=False,
                body={
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                    },
                },
            )
        },
        "/api/v1/auth/register": {
            "post": _operation(
                "ثبت‌نام و دریافت توکن",
                auth=False,
                body={
                    "type": "object",
                    "required": ["first_name", "last_name", "username", "password"],
                    "properties": {
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "phone": {"type": "string"},
                        "email": {"type": "string"},
                    },
                },
            )
        },
        "/api/v1/auth/logout": _path("post", "باطل کردن توکن جاری"),
        "/api/v1/auth/me": _path("get", "کاربر واردشده"),
    }
    for route in DASHBOARD_ROUTES:
        method = route["method"].lower()
        paths.setdefault(route["path"], {})[method] = _operation(
            f"{route['domain']}.{route['tool']}",
            body={"type": "object"} if method in {"post", "patch", "put"} else None,
            path_id="{id}" in route["path"],
        )
    for group in catalog:
        domain = group["domain"]
        for tool in group.get("tools") or []:
            path = f"/api/v1/{domain}/tools/{tool['name']}"
            schema = tool.get("parameters") or {"type": "object"}
            entry = paths.setdefault(path, {})
            entry["post"] = _operation(tool.get("title") or tool["name"], body=schema)
            if tool.get("read_only"):
                entry["get"] = _operation(tool.get("title") or tool["name"], body=None)
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Management API",
            "version": "1",
            "description": "ورود با توکن Bearer و سپس ابزارهای دامنه یا مسیرهای داشبورد.",
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"},
            }
        },
        "paths": paths,
    }


def _path(method: str, summary: str, auth: bool = True, body: dict | None = None) -> dict:
    return {method: _operation(summary, auth=auth, body=body)}


def _operation(summary: str, auth: bool = True, body: dict | None = None, path_id: bool = False) -> dict:
    operation = {"summary": summary, "responses": {"200": {"description": "پاکت JSON"}}}
    if auth:
        operation["security"] = [{"bearerAuth": []}]
    if path_id:
        operation["parameters"] = [
            {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}},
        ]
    if body is not None:
        operation["requestBody"] = {
            "required": True,
            "content": {"application/json": {"schema": body}},
        }
    return operation
