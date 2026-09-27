"""اعتبارسنجی ورودی ابزارهای ممیزی."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_get_audit_log(row_id: int) -> int:
    """شناسه خواندن ممیزی را با اسکیما بررسی می‌کند."""
    from schemas.crud.audit_log import GetAuditLogInput

    return parse_id(GetAuditLogInput, row_id)


def validate_list_audit_logs(
    entity=None,
    entity_id=None,
    user_id=None,
    limit=None,
    offset=None,
) -> dict:
    """صفحه‌بندی و فیلتر فهرست ممیزی را با اسکیما بررسی می‌کند."""
    from schemas.crud.audit_log import ListAuditLogsInput

    return parse_optional(ListAuditLogsInput, entity=entity, entity_id=entity_id, user_id=user_id, limit=limit, offset=offset)


validate_get_audit_log = logged_step("validate")(validate_get_audit_log)
validate_list_audit_logs = logged_step("validate")(validate_list_audit_logs)
