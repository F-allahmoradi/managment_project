"""دامنهٔ تعریف یادآوری: متن، زمان، تکرار، گیرنده، وضعیت پیگیری.

ارسال کانال در dispatcher است. برای هر گیرنده یک
follow_up_states با «در انتظار» و attempt_count = 0 ساخته می‌شود.
"""

from auth.permissions import user_has_permission
from errors.crud import (
    InvalidInputError,
    PermissionDeniedError,
    ReminderNotFoundError,
)
from repository import users_share_active_project_record
from logging_module import logged_step
from services.external_contact import fetch_external_contact
from services.project import fetch_active_membership, fetch_project
from services.user import fetch_user

from business_logic.repository import (
    count_execution_logs,
    fetch_follow_up_state_records,
    fetch_reminder_record,
    fetch_reminders_for_actor_records,
    insert_reminder_graph,
    reminder_targets_user,
    resolve_lookup_id,
    update_reminder_row,
)


def _not_found_message(reminder_id: int) -> str:
    return f"یادآوری با شناسه {reminder_id} پیدا نشد"


def assert_one_target(user_id, external_contact_id) -> None:
    """اگر هر دو پر یا هر دو خالی باشند قبل از INSERT خطا می‌دهد."""
    has_user = user_id is not None
    has_external = external_contact_id is not None
    if has_user == has_external:
        raise InvalidInputError(
            "گیرنده باید دقیقاً یکی از کاربر سامانه یا مخاطب خارجی باشد"
        )


def prepare_target(user_id, external_contact_id) -> dict:
    """هدف گیرنده را با XOR و وجود ردیف می‌سنجد."""
    assert_one_target(user_id, external_contact_id)
    if user_id is not None:
        user = fetch_user(user_id)
        if not user["is_active"]:
            raise InvalidInputError("کاربر غیرفعال نمی‌تواند گیرنده باشد")
        return {"user_id": user_id, "external_contact_id": None}
    contact = fetch_external_contact(external_contact_id)
    if not contact["is_active"]:
        raise InvalidInputError("مخاطب خارجی غیرفعال است")
    return {"user_id": None, "external_contact_id": external_contact_id}


def collect_targets(fields: dict) -> list:
    """گیرنده‌های create را می‌سازد؛ حداقل یکی لازم است.

    هر فیلد یک ردیف جدا است. XOR روی همان ردیف است، نه روی کل یادآوری.
    """
    targets = []
    if fields.get("target_user_id") is not None:
        targets.append(prepare_target(fields["target_user_id"], None))
    if fields.get("target_external_contact_id") is not None:
        targets.append(prepare_target(None, fields["target_external_contact_id"]))
    if not targets:
        raise InvalidInputError("حداقل یک گیرنده لازم است")
    return targets


def fetch_reminder(reminder_id: int) -> dict:
    """یک یادآوری را با شناسه می‌خواند؛ بدون بررسی دسترسی."""
    row = fetch_reminder_record(reminder_id)
    if row is None:
        raise ReminderNotFoundError(_not_found_message(reminder_id))
    return row


def actor_can_see_reminder(user_id: int, reminder: dict) -> bool:
    """سازنده، گیرندهٔ کاربر، یا عضو فعال پروژه می‌تواند ببیند."""
    if reminder["created_by_user_id"] == user_id:
        return True
    if reminder_targets_user(reminder["id"], user_id):
        return True
    project_id = reminder.get("project_id")
    if project_id is not None:
        return fetch_active_membership(project_id, user_id) is not None
    return False


def require_reminder_access(user_id: int, reminder_id: int) -> dict:
    """اگر یادآوری نباشد یا قابل‌مشاهده نباشد خطا می‌دهد."""
    reminder = fetch_reminder(reminder_id)
    if actor_can_see_reminder(user_id, reminder):
        return reminder
    raise PermissionDeniedError("به این یادآوری دسترسی ندارید")


def require_reminder_write(user_id: int, reminder: dict) -> None:
    """به‌روزرسانی فقط برای سازنده یا عضو فعال پروژه است."""
    project_id = reminder.get("project_id")
    if project_id is not None:
        membership = fetch_active_membership(project_id, user_id)
        if membership is not None:
            return
        raise PermissionDeniedError("عضو فعال این پروژه نیستید")
    if reminder["created_by_user_id"] != user_id:
        raise PermissionDeniedError("فقط سازنده می‌تواند این یادآوری را عوض کند")


def fetch_reminders_for_actor(
    user_id: int,
    limit: int,
    offset: int,
    project_id=None,
) -> list:
    """یادآوری‌های قابل‌مشاهدهٔ کاربر جاری را می‌خواند."""
    return fetch_reminders_for_actor_records(user_id, limit, offset, project_id)


def fetch_follow_up_states(reminder_id: int, limit: int, offset: int) -> list:
    """وضعیت پیگیری گیرنده‌های یک یادآوری را می‌خواند."""
    fetch_reminder(reminder_id)
    return fetch_follow_up_state_records(reminder_id, limit, offset)


def require_reminder_recipient(actor_id: int, target_user_id: int, project_id) -> None:
    """گیرندهٔ اعلان را به خود مدیر، اعضای پروژه‌اش، یا اختیار مدیر کل محدود می‌کند."""
    if user_has_permission(actor_id, "UserRole", "Create"):
        return
    if target_user_id == actor_id:
        return
    if project_id is not None:
        if fetch_active_membership(project_id, target_user_id) is None:
            raise PermissionDeniedError("گیرنده عضو فعال این پروژه نیست")
        return
    if users_share_active_project_record(actor_id, target_user_id):
        return
    raise PermissionDeniedError("اعلان فقط برای خودتان یا اعضای پروژه‌های شماست")


def insert_reminder(fields: dict, created_by: int) -> int:
    """تعریف یادآوری + گیرنده‌ها + follow_up_states را درج می‌کند.

    content_id و task_item_id نوشته نمی‌شوند. execution_logs ساخته نمی‌شود.
    """
    project_id = fields.get("project_id")
    if project_id is not None:
        fetch_project(project_id)
    template = fields.get("message_template")
    if template is None or not str(template).strip():
        raise InvalidInputError("متن یادآوری خالی مجاز نیست")
    targets = collect_targets(fields)
    for target in targets:
        if target.get("user_id") is not None:
            require_reminder_recipient(
                created_by,
                target["user_id"],
                fields.get("project_id"),
            )
    type_id = resolve_lookup_id(
        "reminder_types",
        fields.get("reminder_type_id"),
        fields.get("reminder_type"),
    )
    frequency_id = resolve_lookup_id(
        "reminder_frequencies",
        fields.get("frequency_id"),
        fields.get("frequency"),
    )
    status_id = resolve_lookup_id(
        "reminder_statuses",
        fields.get("status_id"),
        fields.get("status") or "فعال",
    )
    pending_status_id = resolve_lookup_id(
        "follow_up_state_statuses",
        None,
        "در انتظار",
    )
    scheduled_at = fields["scheduled_at"]
    next_run_at = fields.get("next_run_at") or scheduled_at
    return insert_reminder_graph(
        {
            "project_id": project_id,
            "created_by_user_id": created_by,
            "reminder_type_id": type_id,
            "frequency_id": frequency_id,
            "title": fields["title"],
            "message_template": template,
            "scheduled_at": scheduled_at,
            "next_run_at": next_run_at,
            "status_id": status_id,
        },
        targets,
        pending_status_id,
    )


def update_reminder(fields: dict) -> int:
    """تعریف یادآوری موجود را به‌روز می‌کند؛ گیرنده‌ها دست نمی‌خورند."""
    reminder_id = fields.get("id")
    if not isinstance(reminder_id, int) or isinstance(reminder_id, bool) or reminder_id < 1:
        raise InvalidInputError("شناسه یادآوری نامعتبر است")
    fetch_reminder(reminder_id)
    prepared = {"id": reminder_id}
    for key in ("title", "scheduled_at", "next_run_at"):
        if key in fields:
            prepared[key] = fields[key]
    if "message_template" in fields:
        template = fields["message_template"]
        if template is None or not str(template).strip():
            raise InvalidInputError("متن یادآوری خالی مجاز نیست")
        prepared["message_template"] = template
    if "reminder_type_id" in fields or "reminder_type" in fields:
        prepared["reminder_type_id"] = resolve_lookup_id(
            "reminder_types",
            fields.get("reminder_type_id"),
            fields.get("reminder_type"),
        )
    if "frequency_id" in fields or "frequency" in fields:
        prepared["frequency_id"] = resolve_lookup_id(
            "reminder_frequencies",
            fields.get("frequency_id"),
            fields.get("frequency"),
        )
    if "status_id" in fields or "status" in fields:
        prepared["status_id"] = resolve_lookup_id(
            "reminder_statuses",
            fields.get("status_id"),
            fields.get("status"),
        )
    if len(prepared) == 1:
        raise InvalidInputError("حداقل یک فیلد قابل‌به‌روزرسانی لازم است")
    return update_reminder_row(prepared)


def execution_log_count(reminder_id: int) -> int:
    """تعداد لاگ ارسال واقعی همین یادآوری را می‌خواند."""
    return count_execution_logs(reminder_id)


assert_one_target = logged_step("validate")(assert_one_target)
require_reminder_recipient = logged_step("authorize")(require_reminder_recipient)
insert_reminder = logged_step("insert")(insert_reminder)
fetch_reminder = logged_step("fetch")(fetch_reminder)
require_reminder_access = logged_step("authorize")(require_reminder_access)
fetch_reminders_for_actor = logged_step("fetch")(fetch_reminders_for_actor)
fetch_follow_up_states = logged_step("fetch")(fetch_follow_up_states)
update_reminder = logged_step("update")(update_reminder)
execution_log_count = logged_step("fetch")(execution_log_count)
