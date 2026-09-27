"""مسیرهای ثابت داشبورد و شکل کاتالوگ ابزار.

ابزارهای MCP همان منطق دامنه را دارند. HTTP فقط نام را به آدرس
پایدار تبدیل می‌کند و بدنه را به همان تابع می‌دهد.
"""

DASHBOARD_ROUTES = (
    {"method": "GET", "path": "/api/v1/projects", "domain": "crud", "tool": "list_projects"},
    {"method": "GET", "path": "/api/v1/projects/{id}", "domain": "crud", "tool": "get_project"},
    {"method": "POST", "path": "/api/v1/projects", "domain": "crud", "tool": "create_project"},
    {"method": "PATCH", "path": "/api/v1/projects/{id}", "domain": "crud", "tool": "update_project"},
    {"method": "DELETE", "path": "/api/v1/projects/{id}", "domain": "crud", "tool": "delete_project"},
    {"method": "GET", "path": "/api/v1/tasks", "domain": "crud", "tool": "list_tasks"},
    {"method": "GET", "path": "/api/v1/tasks/{id}", "domain": "crud", "tool": "get_task"},
    {"method": "POST", "path": "/api/v1/tasks", "domain": "crud", "tool": "create_task"},
    {"method": "PATCH", "path": "/api/v1/tasks/{id}", "domain": "crud", "tool": "update_task"},
    {"method": "DELETE", "path": "/api/v1/tasks/{id}", "domain": "crud", "tool": "delete_task"},
    {"method": "GET", "path": "/api/v1/task-follow-ups", "domain": "crud", "tool": "list_task_follow_ups"},
    {"method": "POST", "path": "/api/v1/task-follow-ups", "domain": "crud", "tool": "create_task_follow_up"},
    {"method": "GET", "path": "/api/v1/users", "domain": "crud", "tool": "list_users"},
    {"method": "GET", "path": "/api/v1/users/{id}", "domain": "crud", "tool": "get_user"},
    {"method": "POST", "path": "/api/v1/users", "domain": "crud", "tool": "create_user"},
    {"method": "GET", "path": "/api/v1/notifications", "domain": "crud", "tool": "list_notifications"},
    {"method": "GET", "path": "/api/v1/notifications/{id}", "domain": "crud", "tool": "get_notification"},
    {"method": "POST", "path": "/api/v1/notifications/{id}/read", "domain": "crud", "tool": "mark_notification_read"},
    {"method": "GET", "path": "/api/v1/project-members", "domain": "crud", "tool": "list_project_members"},
    {"method": "POST", "path": "/api/v1/project-members", "domain": "crud", "tool": "create_project_member"},
    {"method": "GET", "path": "/api/v1/meetings", "domain": "meeting", "tool": "list_meetings"},
    {"method": "GET", "path": "/api/v1/meetings/{id}", "domain": "meeting", "tool": "get_meeting"},
    {"method": "POST", "path": "/api/v1/meetings", "domain": "meeting", "tool": "create_meeting"},
    {"method": "PATCH", "path": "/api/v1/meetings/{id}", "domain": "meeting", "tool": "update_meeting"},
    {"method": "GET", "path": "/api/v1/reminders", "domain": "reminder", "tool": "list_reminders"},
    {"method": "GET", "path": "/api/v1/reminders/{id}", "domain": "reminder", "tool": "get_reminder"},
    {"method": "POST", "path": "/api/v1/reminders", "domain": "reminder", "tool": "create_reminder"},
)


def merge_route_arguments(route: dict, path_params: dict, payload: dict) -> dict:
    """شناسهٔ مسیر را با بدنه یا کوئری یکی می‌کند.

    ورودی:
        route: یکی از DASHBOARD_ROUTES.
        path_params: پارامترهای مسیر Starlette.
        payload: بدنه JSON یا کوئری.
    خروجی:
        آرگومان آماده برای ابزار.
    """
    arguments = dict(payload)
    if "id" in path_params:
        arguments["id"] = int(path_params["id"])
    return arguments


def tool_is_read_only(tool: dict) -> bool:
    """ابزار خواندنی را از روی برچسب MCP تشخیص می‌دهد."""
    return bool(tool.get("read_only"))
