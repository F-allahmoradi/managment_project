"""ذخیره فایل صوت روی دیسک محلی؛ storage_key مسیر نسبی media است."""

from pathlib import Path
import uuid

from errors.crud import InvalidInputError
from logging_module import logged_step
from paths import MEDIA_ROOT

_SUFFIX_BY_MIME = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
}
_ALLOWED_SUFFIX = frozenset(_SUFFIX_BY_MIME.values())


def _suffix_of(mime_type: str, original_filename: str | None) -> str:
    name_suffix = Path(original_filename or "").suffix.lower()
    if name_suffix in _ALLOWED_SUFFIX:
        return name_suffix
    return _SUFFIX_BY_MIME.get((mime_type or "").split(";")[0].strip(), ".webm")


def _duration_seconds(path: Path) -> int | None:
    try:
        from pydub import AudioSegment

        from business_logic.transcribe import _configure_pydub

        _configure_pydub()
        return max(0, round(len(AudioSegment.from_file(str(path))) / 1000))
    except Exception:
        return None


@logged_step("store")
def store_audio_bytes(
    data: bytes,
    created_by: int,
    mime_type: str,
    original_filename: str | None = None,
) -> dict:
    """بایت صوت را در media می‌نویسد و فیلدهای media_files را برمی‌گرداند."""
    if not data:
        raise InvalidInputError("فایل صوتی خالی است")
    suffix = _suffix_of(mime_type, original_filename)
    key = f"voice/{created_by}/{uuid.uuid4().hex}{suffix}"
    dest = MEDIA_ROOT / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    clean_mime = (mime_type or "audio/webm").split(";")[0].strip() or "audio/webm"
    filename = original_filename or f"recording{suffix}"
    return {
        "storage_key": key,
        "original_filename": Path(filename).name,
        "mime_type": clean_mime,
        "file_size_bytes": len(data),
        "duration_seconds": _duration_seconds(dest),
    }


def resolve_media_path(storage_key: str) -> Path:
    """مسیر فایل را از کلید ذخیره‌سازی با جلوگیری از خروج از media برمی‌گرداند."""
    if not storage_key or Path(storage_key).is_absolute():
        raise InvalidInputError("کلید فایل نامعتبر است")
    dest = (MEDIA_ROOT / storage_key).resolve()
    root = MEDIA_ROOT.resolve()
    if root not in dest.parents and dest != root:
        raise InvalidInputError("کلید فایل نامعتبر است")
    if not dest.is_file():
        raise InvalidInputError("فایل صوتی روی دیسک پیدا نشد")
    return dest
