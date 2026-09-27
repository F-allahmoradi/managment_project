"""سرویس نازک جدول issues، منبع تحلیل، علت، لینک وظیفه، امتیاز، و NER.

عنوان و پروژه و وضعیت seed اینجا است. ساخت وظیفه مال create_task است.
اهمیت و فوریت و شدت و اثر بعد از وصل وظیفه نوشته می‌شوند.
موضوع و موجودیت از خروجی ذخیره‌شدهٔ NER به مسئله وصل می‌شوند.
NER/NLP فقط استخراج می‌کند؛ INSERT مال همین لایه است.
"""

from errors.crud import (
    InvalidInputError,
    IssueNotFoundError,
    TaskNotFoundError,
    TextAnalysisNotFoundError,
)
from logging_module import logged_step
from repository import (
    fetch_first,
    fetch_first_on,
    fetch_issue_cause_record,
    fetch_issue_cause_records,
    fetch_issue_in_project_by_title_record,
    fetch_issue_record,
    fetch_issue_source_records,
    fetch_issue_task_record,
    fetch_issue_task_records,
    fetch_issue_importance_by_id_record,
    fetch_issue_importance_record,
    fetch_issue_urgency_by_id_record,
    fetch_issue_urgency_record,
    fetch_issue_severity_by_id_record,
    fetch_issue_severity_record,
    fetch_issue_impact_record,
    fetch_issue_impact_records,
    fetch_issue_topic_record,
    fetch_issue_topic_records,
    fetch_issue_entity_record,
    fetch_issue_entity_records,
    issue_source_has_topic_record,
    issue_source_has_entity_record,
    fetch_issues_for_actor_records,
    fetch_task_record,
    insert_row_on,
    resolve_lookup_id,
    run_query,
    update_row_on,
)
from repository.columns import unique_messages_for
from services.audit_log import ACTION_CREATE, ACTION_UPDATE, record_audit_on
from services.project import fetch_project
from services.text_analysis import require_text_analysis_access

_DEFAULT_STATUS_NAME = "جدید"
_DEFAULT_CAUSE_LEVEL_NAME = "علت"


def _not_found_message(issue_id: int) -> str:
    return f"مسئله با شناسه {issue_id} پیدا نشد"


def _resolve_status_id(fields: dict) -> int:
    """وضعیت seed را از شناسه، نام فارسی، یا کد انگلیسی برمی‌دارد."""
    status_id = fields.get("status_id")
    status = fields.get("status") or _DEFAULT_STATUS_NAME
    if status_id is not None:
        return resolve_lookup_id("issue_statuses", status_id, None)
    try:
        return resolve_lookup_id("issue_statuses", None, status)
    except InvalidInputError:
        row = fetch_first("issue_statuses", {"code": status})
        if row is None:
            raise InvalidInputError(f"وضعیت مسئله «{status}» پیدا نشد") from None
        if row.get("is_active") is False:
            raise InvalidInputError(f"وضعیت مسئله «{status}» غیرفعال است") from None
        return row["id"]


def _resolve_cause_level_id(fields: dict) -> int:
    """سطح علت seed را از شناسه، نام فارسی، یا کد انگلیسی برمی‌دارد."""
    cause_level_id = fields.get("cause_level_id")
    cause_level = fields.get("cause_level") or _DEFAULT_CAUSE_LEVEL_NAME
    if cause_level_id is not None:
        return resolve_lookup_id("cause_levels", cause_level_id, None)
    try:
        return resolve_lookup_id("cause_levels", None, cause_level)
    except InvalidInputError:
        row = fetch_first("cause_levels", {"code": cause_level})
        if row is None:
            raise InvalidInputError(f"سطح علت «{cause_level}» پیدا نشد") from None
        if row.get("is_active") is False:
            raise InvalidInputError(f"سطح علت «{cause_level}» غیرفعال است") from None
        return row["id"]


def _payload_from_issue(row: dict) -> dict:
    sources = fetch_issue_source_records(row["id"])
    return {
        **row,
        "sources": sources,
        "analysis_ids": [item["analysis_id"] for item in sources],
        "causes": fetch_issue_cause_records(row["id"]),
        "tasks": fetch_issue_task_records(row["id"]),
        "importance": fetch_issue_importance_record(row["id"]),
        "urgency": fetch_issue_urgency_record(row["id"]),
        "severity": fetch_issue_severity_record(row["id"]),
        "impacts": fetch_issue_impact_records(row["id"]),
        "topics": fetch_issue_topic_records(row["id"]),
        "entities": fetch_issue_entity_records(row["id"]),
    }


def fetch_issue(issue_id: int) -> dict:
    """یک مسئله را با منابع تحلیل و حلقهٔ علت می‌خواند؛ بدون بررسی عضویت."""
    row = fetch_issue_record(issue_id)
    if row is None:
        raise IssueNotFoundError(_not_found_message(issue_id))
    return _payload_from_issue(row)


def fetch_issue_project_id(issue_id: int) -> int:
    """شناسه پروژهٔ یک مسئله را برمی‌گرداند."""
    row = fetch_first("issues", {"id": issue_id}, columns=("project_id",))
    if row is None:
        raise IssueNotFoundError(_not_found_message(issue_id))
    return row["project_id"]


def fetch_issues_for_actor(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
) -> list:
    """مسائل پروژه‌هایی را می‌خواند که کاربر عضو فعال‌شان است."""
    rows = fetch_issues_for_actor_records(user_id, limit, offset, project_id)
    return [_payload_from_issue(row) for row in rows]


def _attach_issue_source_on(connection, issue_id: int, analysis_id: int) -> bool:
    """تحلیل را در issue_sources به مسئله وصل می‌کند؛ تکراری را رد می‌کند."""
    existing = fetch_first_on(
        connection,
        "issue_sources",
        {"issue_id": issue_id, "analysis_id": analysis_id},
    )
    if existing is not None:
        return False
    insert_row_on(
        connection,
        "issue_sources",
        {"issue_id": issue_id, "analysis_id": analysis_id},
    )
    return True


def insert_issue(fields: dict, created_by: int) -> dict:
    """مسئله را درج یا با عنوان همین پروژه پیدا می‌کند و تحلیل را وصل می‌کند."""
    project_id = fields["project_id"]
    fetch_project(project_id)
    analysis_id = fields["analysis_id"]
    try:
        require_text_analysis_access(analysis_id, created_by)
    except TextAnalysisNotFoundError:
        raise
    title = fields["title"]
    existing = fetch_issue_in_project_by_title_record(project_id, title)
    if existing is not None:
        issue_id = existing["id"]

        def attach(connection):
            attached = _attach_issue_source_on(connection, issue_id, analysis_id)
            if attached:
                record_audit_on(
                    connection,
                    created_by,
                    ACTION_UPDATE,
                    "Issue",
                    issue_id,
                    None,
                    {"analysis_id": analysis_id, "reused": True},
                )
            return issue_id

        run_query(attach, unique_messages_for("issue_sources"))
        packed = fetch_issue(issue_id)
        packed["reused"] = True
        return packed

    status_id = _resolve_status_id(fields)
    values = {
        "project_id": project_id,
        "status_id": status_id,
        "title": title,
        "created_by_user_id": created_by,
    }

    def work(connection):
        issue_id = insert_row_on(connection, "issues", values)
        insert_row_on(
            connection,
            "issue_sources",
            {"issue_id": issue_id, "analysis_id": analysis_id},
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Issue",
            issue_id,
            None,
            {
                "project_id": project_id,
                "title": title,
                "analysis_id": analysis_id,
            },
        )
        return issue_id

    new_id = run_query(work)
    packed = fetch_issue(new_id)
    packed["reused"] = False
    return packed


def find_issue_in_project(project_id: int, title: str):
    """مسئلهٔ موجود همین پروژه با همین عنوان را برمی‌گرداند یا None."""
    return fetch_issue_in_project_by_title_record(project_id, title)


def fetch_issue_cause(row_id: int) -> dict:
    """یک حلقهٔ علت را می‌خواند."""
    row = fetch_issue_cause_record(row_id)
    if row is None:
        raise IssueNotFoundError(f"حلقهٔ علت با شناسه {row_id} پیدا نشد")
    return row


def insert_issue_cause(fields: dict, created_by: int) -> dict:
    """دو مسئله را در issue_causes با سطح علت یا ریشه وصل می‌کند."""
    issue_id = fields["issue_id"]
    cause_issue_id = fields["cause_issue_id"]
    if issue_id == cause_issue_id:
        raise InvalidInputError("مسئله نمی‌تواند علت خودش باشد")
    effect = fetch_issue_record(issue_id)
    if effect is None:
        raise IssueNotFoundError(_not_found_message(issue_id))
    cause = fetch_issue_record(cause_issue_id)
    if cause is None:
        raise IssueNotFoundError(_not_found_message(cause_issue_id))
    if effect["project_id"] != cause["project_id"]:
        raise InvalidInputError("علت باید در همان پروژهٔ مسئله باشد")
    cause_level_id = _resolve_cause_level_id(fields)

    def work(connection):
        row_id = insert_row_on(
            connection,
            "issue_causes",
            {
                "issue_id": issue_id,
                "cause_issue_id": cause_issue_id,
                "cause_level_id": cause_level_id,
            },
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Issue",
            issue_id,
            None,
            {
                "cause_issue_id": cause_issue_id,
                "cause_level_id": cause_level_id,
            },
        )
        return row_id

    new_id = run_query(work, unique_messages_for("issue_causes"))
    return fetch_issue_cause(new_id)


def fetch_issue_task(row_id: int) -> dict:
    """یک حلقهٔ مسئله-وظیفه را می‌خواند."""
    row = fetch_issue_task_record(row_id)
    if row is None:
        raise IssueNotFoundError(f"حلقهٔ وظیفه با شناسه {row_id} پیدا نشد")
    return row


def _link_analysis_outputs_on(connection, sources: list, task_id: int) -> list:
    """همان تحلیل‌های مسئله را در analysis_outputs به tasks.id وصل می‌کند."""
    output_type = fetch_first_on(connection, "analysis_output_types", {"code": "task"})
    if output_type is None:
        raise InvalidInputError("نوع خروجی تحلیل «وظیفه» پیدا نشد")
    analysis_ids = []
    for source in sources:
        analysis_id = source["analysis_id"]
        existing = fetch_first_on(
            connection,
            "analysis_outputs",
            {
                "analysis_id": analysis_id,
                "output_type_id": output_type["id"],
                "record_id": task_id,
            },
        )
        if existing is None:
            insert_row_on(
                connection,
                "analysis_outputs",
                {
                    "analysis_id": analysis_id,
                    "output_type_id": output_type["id"],
                    "record_id": task_id,
                },
            )
        analysis_ids.append(analysis_id)
    return analysis_ids


def insert_issue_task(fields: dict, created_by: int) -> dict:
    """وظیفهٔ موجود را در issue_tasks به مسئله وصل می‌کند."""
    issue_id = fields["issue_id"]
    task_id = fields["task_id"]
    issue = fetch_issue_record(issue_id)
    if issue is None:
        raise IssueNotFoundError(_not_found_message(issue_id))
    task = fetch_task_record(task_id)
    if task is None:
        raise TaskNotFoundError(f"وظیفه با شناسه {task_id} پیدا نشد")
    if issue["project_id"] != task["project_id"]:
        raise InvalidInputError("وظیفه باید در همان پروژهٔ مسئله باشد")
    sources = fetch_issue_source_records(issue_id)

    def work(connection):
        row_id = insert_row_on(
            connection,
            "issue_tasks",
            {"issue_id": issue_id, "task_id": task_id},
        )
        analysis_ids = _link_analysis_outputs_on(connection, sources, task_id)
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Issue",
            issue_id,
            None,
            {"task_id": task_id, "analysis_ids": analysis_ids},
        )
        return row_id, analysis_ids

    new_id, analysis_ids = run_query(
        work,
        {
            **unique_messages_for("issue_tasks"),
            **unique_messages_for("analysis_outputs"),
        },
    )
    packed = fetch_issue_task(new_id)
    packed["analysis_ids"] = analysis_ids
    return packed


def _resolve_named_lookup(entity_key: str, lookup_id, name) -> int:
    """شناسه lookup را از شناسه یا نام فارسی برمی‌دارد."""
    return resolve_lookup_id(entity_key, lookup_id, name)


def _resolve_lookup_with_code(entity_key: str, lookup_id, name, label: str) -> int:
    """شناسه lookup را از شناسه، نام فارسی، یا کد انگلیسی برمی‌دارد."""
    if lookup_id is not None:
        return resolve_lookup_id(entity_key, lookup_id, None)
    try:
        return resolve_lookup_id(entity_key, None, name)
    except InvalidInputError:
        row = fetch_first(entity_key, {"code": name})
        if row is None:
            raise InvalidInputError(f"{label} «{name}» پیدا نشد") from None
        if row.get("is_active") is False:
            raise InvalidInputError(f"{label} «{name}» غیرفعال است") from None
        return row["id"]


def _upsert_unique_on(connection, entity_key, where: dict, values: dict):
    """ردیف یک‌به‌یک را درج یا به‌روز می‌کند."""
    existing = fetch_first_on(connection, entity_key, where)
    if existing is None:
        row_id = insert_row_on(connection, entity_key, {**where, **values})
        return row_id, True
    update_row_on(
        connection,
        entity_key,
        {"id": existing["id"], **values},
        IssueNotFoundError,
        "ردیف امتیاز پیدا نشد",
    )
    return existing["id"], False


def _sync_analysis_lookup_on(
    connection,
    sources: list,
    entity_key: str,
    fk_name: str,
    lookup_id: int,
) -> list:
    """همان مقدار امتیاز را روی تحلیل‌های مبدأ مسئله می‌نویسد."""
    analysis_ids = []
    for source in sources:
        analysis_id = source["analysis_id"]
        _upsert_unique_on(
            connection,
            entity_key,
            {"analysis_id": analysis_id},
            {fk_name: lookup_id},
        )
        analysis_ids.append(analysis_id)
    return analysis_ids


def _require_issue(issue_id: int) -> dict:
    issue = fetch_issue_record(issue_id)
    if issue is None:
        raise IssueNotFoundError(_not_found_message(issue_id))
    return issue


def set_issue_importance(fields: dict, created_by: int) -> dict:
    """اهمیت مسئله را از task_importances می‌نویسد و روی تحلیل مبدأ هم می‌گذارد."""
    issue_id = fields["issue_id"]
    _require_issue(issue_id)
    importance_id = _resolve_named_lookup(
        "task_importances",
        fields.get("importance_id"),
        fields.get("importance"),
    )
    sources = fetch_issue_source_records(issue_id)

    def work(connection):
        row_id, created = _upsert_unique_on(
            connection,
            "issue_importances",
            {"issue_id": issue_id},
            {"importance_id": importance_id},
        )
        analysis_ids = _sync_analysis_lookup_on(
            connection,
            sources,
            "text_analysis_importances",
            "importance_id",
            importance_id,
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE if created else ACTION_UPDATE,
            "Issue",
            issue_id,
            None,
            {"importance_id": importance_id, "analysis_ids": analysis_ids},
        )
        return row_id, analysis_ids

    row_id, analysis_ids = run_query(
        work,
        {
            **unique_messages_for("issue_importances"),
            **unique_messages_for("text_analysis_importances"),
        },
    )
    packed = fetch_issue_importance_by_id_record(row_id)
    packed["analysis_ids"] = analysis_ids
    return packed


def set_issue_urgency(fields: dict, created_by: int) -> dict:
    """فوریت مسئله را از task_priorities می‌نویسد و روی تحلیل مبدأ هم می‌گذارد."""
    issue_id = fields["issue_id"]
    _require_issue(issue_id)
    priority_id = _resolve_named_lookup(
        "task_priorities",
        fields.get("priority_id"),
        fields.get("priority"),
    )
    sources = fetch_issue_source_records(issue_id)

    def work(connection):
        row_id, created = _upsert_unique_on(
            connection,
            "issue_urgencies",
            {"issue_id": issue_id},
            {"priority_id": priority_id},
        )
        analysis_ids = _sync_analysis_lookup_on(
            connection,
            sources,
            "text_analysis_urgencies",
            "priority_id",
            priority_id,
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE if created else ACTION_UPDATE,
            "Issue",
            issue_id,
            None,
            {"priority_id": priority_id, "analysis_ids": analysis_ids},
        )
        return row_id, analysis_ids

    row_id, analysis_ids = run_query(
        work,
        {
            **unique_messages_for("issue_urgencies"),
            **unique_messages_for("text_analysis_urgencies"),
        },
    )
    packed = fetch_issue_urgency_by_id_record(row_id)
    packed["analysis_ids"] = analysis_ids
    return packed


def set_issue_severity(fields: dict, created_by: int) -> dict:
    """شدت مسئله را از severity_levels می‌نویسد."""
    issue_id = fields["issue_id"]
    _require_issue(issue_id)
    severity_id = _resolve_lookup_with_code(
        "severity_levels",
        fields.get("severity_id"),
        fields.get("severity"),
        "شدت مسئله",
    )

    def work(connection):
        row_id, created = _upsert_unique_on(
            connection,
            "issue_severities",
            {"issue_id": issue_id},
            {"severity_id": severity_id},
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE if created else ACTION_UPDATE,
            "Issue",
            issue_id,
            None,
            {"severity_id": severity_id},
        )
        return row_id

    row_id = run_query(work, unique_messages_for("issue_severities"))
    return fetch_issue_severity_by_id_record(row_id)


def fetch_issue_impact(row_id: int) -> dict:
    """یک اثر مسئله را می‌خواند."""
    row = fetch_issue_impact_record(row_id)
    if row is None:
        raise IssueNotFoundError(f"اثر مسئله با شناسه {row_id} پیدا نشد")
    return row


def add_issue_impact(fields: dict, created_by: int) -> dict:
    """یک اثر با نوع seed از impact_types به مسئله اضافه می‌کند."""
    issue_id = fields["issue_id"]
    _require_issue(issue_id)
    impact_type_id = _resolve_lookup_with_code(
        "impact_types",
        fields.get("impact_type_id"),
        fields.get("impact_type"),
        "نوع اثر",
    )
    description = fields.get("description")
    if not description:
        type_row = fetch_first("impact_types", {"id": impact_type_id})
        description = (type_row or {}).get("name") or ""
    if not description:
        raise InvalidInputError("شرح اثر خالی است")

    def work(connection):
        row_id = insert_row_on(
            connection,
            "issue_impacts",
            {
                "issue_id": issue_id,
                "impact_type_id": impact_type_id,
                "description": description,
            },
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Issue",
            issue_id,
            None,
            {"impact_type_id": impact_type_id, "description": description},
        )
        return row_id

    new_id = run_query(work)
    return fetch_issue_impact(new_id)


def fetch_issue_topic(row_id: int) -> dict:
    """یک حلقهٔ مسئله-موضوع را می‌خواند."""
    row = fetch_issue_topic_record(row_id)
    if row is None:
        raise IssueNotFoundError(f"حلقهٔ موضوع با شناسه {row_id} پیدا نشد")
    return row


def insert_issue_topic(fields: dict, created_by: int) -> dict:
    """موضوع ذخیره‌شدهٔ تحلیل مبدأ را در issue_topics به مسئله وصل می‌کند."""
    issue_id = fields["issue_id"]
    _require_issue(issue_id)
    topic_id = _resolve_lookup_with_code(
        "topics",
        fields.get("topic_id"),
        fields.get("topic"),
        "موضوع",
    )
    if issue_source_has_topic_record(issue_id, topic_id) is None:
        raise InvalidInputError("موضوع باید از تحلیل ذخیره‌شدهٔ همین مسئله باشد")

    def work(connection):
        row_id = insert_row_on(
            connection,
            "issue_topics",
            {"issue_id": issue_id, "topic_id": topic_id},
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Issue",
            issue_id,
            None,
            {"topic_id": topic_id},
        )
        return row_id

    new_id = run_query(work, unique_messages_for("issue_topics"))
    return fetch_issue_topic(new_id)


def fetch_issue_entity(row_id: int) -> dict:
    """یک حلقهٔ مسئله-موجودیت را می‌خواند."""
    row = fetch_issue_entity_record(row_id)
    if row is None:
        raise IssueNotFoundError(f"حلقهٔ موجودیت با شناسه {row_id} پیدا نشد")
    return row


def insert_issue_entity(fields: dict, created_by: int) -> dict:
    """موجودیت ذخیره‌شدهٔ NER را با نقش seed در issue_entities وصل می‌کند."""
    issue_id = fields["issue_id"]
    _require_issue(issue_id)
    entity_id = fields["entity_id"]
    entity = fetch_first("entities", {"id": entity_id})
    if entity is None:
        raise InvalidInputError(f"موجودیت با شناسه {entity_id} پیدا نشد")
    if issue_source_has_entity_record(issue_id, entity_id) is None:
        raise InvalidInputError("موجودیت باید از تحلیل ذخیره‌شدهٔ همین مسئله باشد")
    role_id = _resolve_lookup_with_code(
        "issue_entity_roles",
        fields.get("role_id"),
        fields.get("role"),
        "نقش موجودیت مسئله",
    )

    def work(connection):
        row_id = insert_row_on(
            connection,
            "issue_entities",
            {
                "issue_id": issue_id,
                "entity_id": entity_id,
                "role_id": role_id,
            },
        )
        record_audit_on(
            connection,
            created_by,
            ACTION_CREATE,
            "Issue",
            issue_id,
            None,
            {"entity_id": entity_id, "role_id": role_id},
        )
        return row_id

    new_id = run_query(work, unique_messages_for("issue_entities"))
    return fetch_issue_entity(new_id)


insert_issue = logged_step("insert")(insert_issue)
insert_issue_cause = logged_step("insert")(insert_issue_cause)
insert_issue_task = logged_step("insert")(insert_issue_task)
set_issue_importance = logged_step("update")(set_issue_importance)
set_issue_urgency = logged_step("update")(set_issue_urgency)
set_issue_severity = logged_step("update")(set_issue_severity)
add_issue_impact = logged_step("insert")(add_issue_impact)
insert_issue_topic = logged_step("insert")(insert_issue_topic)
insert_issue_entity = logged_step("insert")(insert_issue_entity)
fetch_issue = logged_step("fetch")(fetch_issue)
fetch_issues_for_actor = logged_step("fetch")(fetch_issues_for_actor)
find_issue_in_project = logged_step("fetch")(find_issue_in_project)
