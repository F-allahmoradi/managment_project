"""اعتبارسنجی ورودی ابزارهای ExternalContact."""

from logging_module import logged_step
from validators.common import parse_id, parse_optional


def validate_create_external_contact(fields: dict) -> dict:
    """ورودی ثبت مخاطب خارجی را با اسکیما بررسی می‌کند."""
    from schemas.crud.external_contact import CreateExternalContactInput

    return CreateExternalContactInput(**fields).model_dump()


def validate_get_external_contact(contact_id: int) -> int:
    """شناسه خواندن مخاطب خارجی را با اسکیما بررسی می‌کند."""
    from schemas.crud.external_contact import GetExternalContactInput

    return parse_id(GetExternalContactInput, contact_id)


def validate_list_external_contacts(limit=None, offset=None) -> dict:
    """صفحه‌بندی فهرست مخاطبان خارجی را با اسکیما بررسی می‌کند."""
    from schemas.crud.external_contact import ListExternalContactsInput

    return parse_optional(ListExternalContactsInput, limit=limit, offset=offset)


validate_create_external_contact = logged_step("validate")(
    validate_create_external_contact
)
validate_get_external_contact = logged_step("validate")(validate_get_external_contact)
validate_list_external_contacts = logged_step("validate")(
    validate_list_external_contacts
)
