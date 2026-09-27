"""کمک‌های مشترک پاسخ HTTP برای وب و موبایل.

مجوز دامنه هنوز در auth.gate است. اینجا فقط شکل هدر و کد وضعیت است.
"""

PERMISSION_DENIED = "PERMISSION_DENIED"
ACTOR_NOT_FOUND = "ACTOR_NOT_FOUND"
INVALID_INPUT = "INVALID_INPUT"
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
UNAUTHENTICATED = "UNAUTHENTICATED"
UNKNOWN_DOMAIN = "UNKNOWN_DOMAIN"
UNKNOWN_TOOL = "UNKNOWN_TOOL"
METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
DOMAIN_UNAVAILABLE = "DOMAIN_UNAVAILABLE"
QUERY_TIMEOUT = "QUERY_TIMEOUT"
DATABASE_ERROR = "DATABASE_ERROR"
PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"

_NOT_FOUND_SUFFIX = "_NOT_FOUND"


def extract_bearer(header: str | None) -> str | None:
    """توکن را از هدر Authorization برمی‌دارد.

    ورودی:
        header: مقدار خام هدر؛ ممکن است خالی باشد.
    خروجی:
        خود توکن، یا None اگر طرح Bearer نباشد.
    """
    if not header:
        return None
    scheme, _, token = header.strip().partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def error_body(error_code: str, message: str) -> dict:
    """پاکت خطای JSON را هم‌شکل ابزارهای MCP می‌سازد."""
    return {"status": "error", "error_code": error_code, "message": message}


def http_status_for(payload: dict) -> int:
    """کد HTTP را از پاکت status/error_code برمی‌گرداند.

    موفقیت ۲۰۰ است. بقیه از روی error_code ثابت می‌مانند تا کلاینت
    هم به بدنه و هم به وضعیت HTTP تکیه کند.
    """
    if payload.get("status") != "error":
        return 200
    code = str(payload.get("error_code") or "")
    if code in {UNAUTHENTICATED, INVALID_CREDENTIALS, ACTOR_NOT_FOUND}:
        return 401
    if code in {PERMISSION_DENIED, ACCOUNT_INACTIVE}:
        return 403
    if code in {UNKNOWN_DOMAIN, UNKNOWN_TOOL} or code.endswith(_NOT_FOUND_SUFFIX):
        return 404
    if code == METHOD_NOT_ALLOWED:
        return 405
    if code == PAYLOAD_TOO_LARGE:
        return 413
    if code == INVALID_INPUT:
        return 422
    if code == DOMAIN_UNAVAILABLE:
        return 503
    if code == QUERY_TIMEOUT:
        return 504
    return 500
