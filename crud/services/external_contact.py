"""سرویس عملیات جدول external_contacts.

مخاطب خارجی حساب کاربری ندارد و در users درج نمی‌شود.
"""

from errors.crud import ExternalContactNotFoundError, InvalidInputError
from logging_module import logged_step
from repository import fetch_row, fetch_rows, insert_row
from services.audit_log import ACTION_CREATE, record_audit


def _not_found_message(contact_id: int) -> str:
    return f"مخاطب خارجی با شناسه {contact_id} پیدا نشد"


def fetch_external_contact(contact_id: int) -> dict:
    """یک مخاطب خارجی را با شناسه می‌خواند."""
    if not isinstance(contact_id, int) or isinstance(contact_id, bool) or contact_id < 1:
        raise InvalidInputError("شناسه مخاطب خارجی نامعتبر است")
    return fetch_row(
        "external_contacts",
        contact_id,
        ExternalContactNotFoundError,
        _not_found_message(contact_id),
    )


def fetch_external_contacts(limit: int, offset: int) -> list:
    """مخاطبان خارجی را با صفحه‌بندی می‌خواند."""
    return fetch_rows("external_contacts", limit, offset)


def insert_external_contact(fields: dict, actor_id=None) -> int:
    """یک مخاطب خارج از سامانه را درج می‌کند؛ ردیف users ساخته نمی‌شود."""
    new_id = insert_row(
        "external_contacts",
        {
            "name": fields["name"],
            "phone": fields.get("phone"),
            "email": fields.get("email"),
            "telegram_id": fields.get("telegram_id"),
            "is_active": fields.get("is_active", True),
        },
    )
    record_audit(
        actor_id,
        ACTION_CREATE,
        "ExternalContact",
        new_id,
        None,
        {"name": fields["name"]},
    )
    return new_id


insert_external_contact = logged_step("insert")(insert_external_contact)
fetch_external_contact = logged_step("fetch")(fetch_external_contact)
fetch_external_contacts = logged_step("fetch")(fetch_external_contacts)
