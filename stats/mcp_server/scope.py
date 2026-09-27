"""محدوده و مجوز مشترک ابزارهای آمار.

عضویت فعال همان منطق گام ۵ است؛ ابزارها INSERT نمی‌زنند.
"""

from auth.gate import (
    require_active_project_member,
    require_permission,
    require_project_permission,
)
from schemas.input import validate_optional_project, validate_project_id


def actor_for_project(resource: str, action: str, project_id: int):
    """مجوز سراسری و عضویت فعال همان پروژه را می‌سنجد."""
    parsed = validate_project_id(project_id)
    actor = require_project_permission(resource, action, parsed)
    return actor, parsed


def actor_for_optional_project(resource: str, action: str, project_id):
    """مجوز سراسری را می‌سنجد و اگر پروژه آمده باشد عضویت را هم می‌سنجد."""
    actor = require_permission(resource, action)
    parsed = validate_optional_project(project_id)["project_id"]
    if parsed is not None:
        require_active_project_member(actor["id"], parsed)
    return actor, parsed
