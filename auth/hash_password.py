"""هش رمز عبور با PBKDF2 برای ستون password_hash.

رمز خام در PostgreSQL ذخیره نمی‌شود. قالب رشته:
pbkdf2_sha256$تعداد تکرار$نمک هگز$هش هگز

اجرای CLI از ریشه مخزن: python -m auth.hash_password رمز
"""

from hashlib import pbkdf2_hmac
from hmac import compare_digest
import os
import sys

SCHEME = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 150_000
SALT_BYTES = 16


def hash_password(password: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    """رمز خام را به رشته قابل ذخیره در users.password_hash تبدیل می‌کند.

    ورودی:
        password: رمز خام کاربر.
        iterations: تعداد تکرار PBKDF2؛ پیش‌فرض ۱۵۰۰۰۰.
    خروجی:
        رشته با طرح و نمک و هش.
    فراخوانی‌ها:
        os.urandom، pbkdf2_hmac.
    علت:
        INSERT و UPDATE کاربر نباید رمز را به‌صورت متن ساده بنویسند.
    """
    if not password:
        raise ValueError("رمز خالی مجاز نیست")
    salt = os.urandom(SALT_BYTES)
    digest = pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return f"{SCHEME}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """رمز خام را با هش ذخیره‌شده مقایسه می‌کند.

    ورودی:
        password: رمز واردشده.
        stored: مقدار password_hash در جدول users.
    خروجی:
        True فقط اگر هش یکی باشد.
    فراخوانی‌ها:
        pbkdf2_hmac، compare_digest.
    علت:
        compare_digest برای جلوگیری از مقایسه زمانی است.
        ورود کامل هنوز در این گام نیست؛ تست صحت هش از همین استفاده می‌کند.
    """
    if not password or not stored:
        return False
    parts = stored.split("$")
    if len(parts) != 4 or parts[0] != SCHEME:
        return False
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
    except ValueError:
        return False
    digest = pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return compare_digest(digest, expected)


def main(argv: list[str] | None = None) -> int:
    """هش PBKDF2 را روی stdout چاپ می‌کند.

    ورودی:
        argv: آرگومان‌ها؛ اگر None باشد از sys.argv می‌خواند.
    خروجی:
        ۰ در موفقیت، ۱ اگر رمز خالی باشد.
    فراخوانی‌ها:
        hash_password.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        password = args[0]
    else:
        password = sys.stdin.readline().rstrip("\n")
    if not password:
        sys.stderr.write("رمز خالی است\n")
        return 1
    sys.stdout.write(hash_password(password) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
