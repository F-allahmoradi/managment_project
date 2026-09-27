"""اعتبارسنجی ورودی ابزارهای Issue."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_create_issue(fields: dict) -> dict:
    """ورودی ثبت مسئله را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import CreateIssueInput

    return CreateIssueInput(**fields).model_dump()


def validate_get_issue(issue_id: int) -> int:
    """شناسه خواندن مسئله را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import GetIssueInput

    return parse_id(GetIssueInput, issue_id)


def validate_list_issues(project_id=None, limit=None, offset=None) -> dict:
    """صفحه‌بندی و فیلتر پروژهٔ فهرست مسائل را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import ListIssuesInput

    return parse_optional(
        ListIssuesInput,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )


def validate_link_issue_cause(fields: dict) -> dict:
    """ورودی وصل علت را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import LinkIssueCauseInput

    return LinkIssueCauseInput(**fields).model_dump()


def validate_link_issue_task(fields: dict) -> dict:
    """ورودی وصل وظیفه به مسئله را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import LinkIssueTaskInput

    return LinkIssueTaskInput(**fields).model_dump()


def validate_set_issue_importance(fields: dict) -> dict:
    """ورودی تنظیم اهمیت مسئله را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import SetIssueImportanceInput

    return SetIssueImportanceInput(**fields).model_dump()


def validate_set_issue_urgency(fields: dict) -> dict:
    """ورودی تنظیم فوریت مسئله را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import SetIssueUrgencyInput

    return SetIssueUrgencyInput(**fields).model_dump()


def validate_set_issue_severity(fields: dict) -> dict:
    """ورودی تنظیم شدت مسئله را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import SetIssueSeverityInput

    return SetIssueSeverityInput(**fields).model_dump()


def validate_add_issue_impact(fields: dict) -> dict:
    """ورودی افزودن اثر مسئله را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import AddIssueImpactInput

    return AddIssueImpactInput(**fields).model_dump()


def validate_link_issue_topic(fields: dict) -> dict:
    """ورودی وصل موضوع به مسئله را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import LinkIssueTopicInput

    return LinkIssueTopicInput(**fields).model_dump()


def validate_link_issue_entity(fields: dict) -> dict:
    """ورودی وصل موجودیت به مسئله را با اسکیما بررسی می‌کند."""
    from schemas.crud.issue import LinkIssueEntityInput

    return LinkIssueEntityInput(**fields).model_dump()


validate_create_issue = logged_step("validate")(validate_create_issue)
validate_get_issue = logged_step("validate")(validate_get_issue)
validate_list_issues = logged_step("validate")(validate_list_issues)
validate_link_issue_cause = logged_step("validate")(validate_link_issue_cause)
validate_link_issue_task = logged_step("validate")(validate_link_issue_task)
validate_set_issue_importance = logged_step("validate")(validate_set_issue_importance)
validate_set_issue_urgency = logged_step("validate")(validate_set_issue_urgency)
validate_set_issue_severity = logged_step("validate")(validate_set_issue_severity)
validate_add_issue_impact = logged_step("validate")(validate_add_issue_impact)
validate_link_issue_topic = logged_step("validate")(validate_link_issue_topic)
validate_link_issue_entity = logged_step("validate")(validate_link_issue_entity)
