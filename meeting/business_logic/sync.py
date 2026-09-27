"""همگام‌سازی خروجی جلسه به وظیفه و پیام چت پروژه.

ژانر و تصمیم از استخراج متن می‌آید، نه از جدول جدا.
متن از contents.text_body یا notes دستی می‌آید؛ NLP نیست.
"""

from datetime import datetime

from errors.crud import InvalidInputError
from logging_module import logged_step
from repository import insert_row_on, resolve_lookup_id
from repository.db import run_query
from services.audit_log import ACTION_CREATE, ACTION_UPDATE, record_audit_on
from services.content import fetch_content
from services.message_recipient import validate_recipient_target
from services.notification import TYPE_NEW_TASK, insert_notification_on
from services.project import fetch_active_membership, fetch_project
from services.task import fetch_task
from services.user import fetch_user

from business_logic.meetings import require_meeting_access, require_meeting_manager
from business_logic.repository import (
    fetch_sync_item_records,
    fetch_synced_status_id,
    insert_sync_item_on,
    mark_meeting_sync_on,
)

TYPE_EXTERNAL = "مذاکره خارجی"
TYPE_LEGAL = "مذاکره حقوقی"
TYPE_MANAGERS = "مذاکره مدیران"
TASK_STATUS = "شروع نشده"
TASK_PRIORITY = "متوسط"
TASK_IMPORTANCE = "متوسط"


def _text_from(content: dict, notes) -> str:
    """متن همگام را از یادداشت دستی یا text_body محتوا برمی‌دارد."""
    if notes is not None and str(notes).strip():
        return str(notes).strip()
    body = content.get("text_body")
    if body is not None and str(body).strip():
        return str(body).strip()
    return ""


def assert_sync_allowed(meeting: dict, confirm: bool) -> None:
    """قانون visibility و نوع جلسه را برای sync اعمال می‌کند."""
    if meeting.get("project_id") is None or meeting.get("visibility") == "PRIVATE":
        raise InvalidInputError("جلسه خصوصی یا بدون پروژه همگام نمی‌شود")
    if meeting.get("meeting_type_name") == TYPE_MANAGERS:
        raise InvalidInputError("مذاکره مدیران همگام نمی‌شود")
    needs_confirm = meeting.get("visibility") == "RESTRICTED" or meeting.get(
        "meeting_type_name"
    ) in {TYPE_EXTERNAL, TYPE_LEGAL}
    if needs_confirm and not confirm:
        raise InvalidInputError("همگام‌سازی این جلسه نیاز به تأیید دارد")


def _plan_outputs(fields: dict, text: str) -> dict:
    """مشخص می‌کند کدام خروجی‌ها باید ساخته شوند."""
    want_task = fields.get("assigned_to_user_id") is not None
    want_message = fields.get("chat_id") is not None
    return {
        "task": want_task,
        "message": want_message,
        "task_title": fields.get("task_title")
        or fields.get("decision_title")
        or None,
        "assigned_to_user_id": fields.get("assigned_to_user_id"),
        "task_id": fields.get("task_id"),
        "chat_id": fields.get("chat_id"),
        "message_text": fields.get("message_text") or text,
        "recipient_user_id": fields.get("recipient_user_id"),
        "recipient_external_contact_id": fields.get("recipient_external_contact_id"),
    }


def _existing_targets(meeting_id: int) -> dict:
    """اگر از قبل خروجی‌ای لینک شده باشد دوباره ساخته نمی‌شود."""
    found = {"task_id": None, "message_id": None}
    for item in fetch_sync_item_records(meeting_id):
        for key in found:
            if item.get(key) is not None:
                found[key] = item[key]
    return found


def _create_task_on(connection, meeting: dict, actor_id: int, plan: dict, text: str):
    assignee = plan["assigned_to_user_id"]
    user = fetch_user(assignee)
    if user.get("is_active") is False:
        raise InvalidInputError("کاربر غیرفعال را نمی‌توان مسئول کار کرد")
    membership = fetch_active_membership(meeting["project_id"], assignee)
    if membership is None:
        raise InvalidInputError("مسئول باید عضو فعال همین پروژه باشد")
    title = plan["task_title"] or f"وظیفه جلسه: {meeting['title']}"
    status_id = resolve_lookup_id("task_statuses", None, TASK_STATUS)
    priority_id = resolve_lookup_id("task_priorities", None, TASK_PRIORITY)
    importance_id = resolve_lookup_id("task_importances", None, TASK_IMPORTANCE)
    task_id = insert_row_on(
        connection,
        "tasks",
        {
            "project_id": meeting["project_id"],
            "title": title,
            "description": text or None,
            "assigned_to_user_id": assignee,
            "created_by_user_id": actor_id,
            "status_id": status_id,
            "priority_id": priority_id,
            "importance_id": importance_id,
        },
    )
    record_audit_on(
        connection,
        actor_id,
        ACTION_CREATE,
        "Task",
        task_id,
        None,
        {
            "project_id": meeting["project_id"],
            "title": title,
            "assigned_to_user_id": assignee,
            "meeting_id": meeting["id"],
        },
    )
    insert_notification_on(
        connection,
        assignee,
        TYPE_NEW_TASK,
        f"وظیفه {title} به تو اختصاص داده شد.",
    )
    return task_id


def _create_message_on(connection, meeting: dict, actor_id: int, plan: dict, content_id: int):
    recipients = []
    if plan["recipient_user_id"] is not None:
        recipients.append(
            validate_recipient_target(
                plan["chat_id"],
                plan["recipient_user_id"],
                None,
            )
        )
    if plan["recipient_external_contact_id"] is not None:
        recipients.append(
            validate_recipient_target(
                plan["chat_id"],
                None,
                plan["recipient_external_contact_id"],
            )
        )
    if not recipients:
        raise InvalidInputError("برای پیام همگام حداقل یک گیرنده لازم است")
    if not plan["message_text"]:
        raise InvalidInputError("متن پیام همگام خالی است")
    task_id = plan.get("resolved_task_id")
    if task_id is None:
        raise InvalidInputError("برای پیام همگام تسک لازم است")
    task = fetch_task(task_id)
    if task["project_id"] != meeting["project_id"]:
        raise InvalidInputError("تسک باید در همان پروژهٔ جلسه باشد")
    message_id = insert_row_on(
        connection,
        "messages",
        {
            "chat_id": plan["chat_id"],
            "sender_user_id": actor_id,
            "task_id": task_id,
            "text": plan["message_text"],
            "content_id": content_id,
        },
    )
    for recipient in recipients:
        insert_row_on(
            connection,
            "message_recipients",
            {
                "message_id": message_id,
                "user_id": recipient["user_id"],
                "external_contact_id": recipient["external_contact_id"],
            },
        )
    record_audit_on(
        connection,
        actor_id,
        ACTION_CREATE,
        "Message",
        message_id,
        None,
        {
            "chat_id": plan["chat_id"],
            "task_id": task_id,
            "meeting_id": meeting["id"],
        },
    )
    return message_id


def _link_on(connection, meeting_id: int, actor_id: int, **targets) -> int:
    payload = {
        "meeting_id": meeting_id,
        "task_id": None,
        "message_id": None,
        "created_by_user_id": actor_id,
    }
    payload.update(targets)
    return insert_sync_item_on(connection, payload)


def sync_meeting(meeting_id: int, fields: dict, actor_id: int) -> dict:
    """از روی ضبط، وظیفه یا پیام پروژه می‌سازد و در meeting_sync_items لینک می‌گذارد."""
    meeting = require_meeting_access(actor_id, meeting_id)
    require_meeting_manager(actor_id, meeting)
    assert_sync_allowed(meeting, bool(fields.get("confirm")))
    if meeting["sync_status"] == "SYNCED":
        raise InvalidInputError("این جلسه قبلاً همگام شده")
    if meeting["status_name"] == "لغو شده":
        raise InvalidInputError("جلسهٔ لغو شده همگام نمی‌شود")
    if meeting.get("content_id") is None:
        raise InvalidInputError("ابتدا جلسه را ضبط کنید")
    if meeting["status_name"] != "ضبط شده" and meeting["sync_status"] != "PARTIAL":
        raise InvalidInputError("فقط جلسهٔ ضبط‌شده همگام می‌شود")
    fetch_project(meeting["project_id"])
    content = fetch_content(meeting["content_id"])
    text = _text_from(content, fields.get("notes"))
    if not text:
        raise InvalidInputError("برای همگام‌سازی متن ضبط یا یادداشت لازم است")
    plan = _plan_outputs(fields, text)
    existing = _existing_targets(meeting_id)
    planned = 0
    if plan["task"]:
        planned += 1
    if plan["message"]:
        planned += 1
    if planned == 0:
        raise InvalidInputError("برای همگام‌سازی وظیفه یا پیام لازم است")
    skipped = 0
    synced_status_id = fetch_synced_status_id()

    def work(connection):
        created = {
            "task_id": existing["task_id"],
            "message_id": existing["message_id"],
            "sync_item_ids": [],
        }
        nonlocal skipped
        if plan["task"] and created["task_id"] is None:
            try:
                task_id = _create_task_on(connection, meeting, actor_id, plan, text)
            except InvalidInputError:
                skipped += 1
                task_id = None
            if task_id is not None:
                created["task_id"] = task_id
                created["sync_item_ids"].append(
                    _link_on(connection, meeting_id, actor_id, task_id=task_id)
                )
        plan["resolved_task_id"] = created["task_id"] or plan.get("task_id")
        if plan["message"] and created["message_id"] is None:
            try:
                message_id = _create_message_on(
                    connection,
                    meeting,
                    actor_id,
                    plan,
                    meeting["content_id"],
                )
            except InvalidInputError:
                skipped += 1
                message_id = None
            if message_id is not None:
                created["message_id"] = message_id
                created["sync_item_ids"].append(
                    _link_on(
                        connection,
                        meeting_id,
                        actor_id,
                        message_id=message_id,
                    )
                )
        made = sum(
            1
            for key in ("task_id", "message_id")
            if created[key] is not None
        )
        if made == 0:
            raise InvalidInputError("هیچ خروجی‌ای همگام نشد")
        sync_status = "SYNCED" if skipped == 0 and made >= planned else "PARTIAL"
        mark_meeting_sync_on(
            connection,
            meeting_id,
            sync_status,
            synced_status_id,
            datetime.now() if sync_status == "SYNCED" else None,
        )
        record_audit_on(
            connection,
            actor_id,
            ACTION_UPDATE,
            "Meeting",
            meeting_id,
            {"sync_status": meeting["sync_status"]},
            {
                "sync_status": sync_status,
                "task_id": created["task_id"],
                "message_id": created["message_id"],
            },
        )
        created["sync_status"] = sync_status
        return created

    result = run_query(work)
    return {
        "id": meeting_id,
        "sync_status": result["sync_status"],
        "task_id": result["task_id"],
        "message_id": result["message_id"],
        "sync_item_ids": result["sync_item_ids"],
    }


sync_meeting = logged_step("insert")(sync_meeting)
assert_sync_allowed = logged_step("auth")(assert_sync_allowed)
