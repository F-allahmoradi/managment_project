"""ذخیرهٔ عکس، فیلم و فایل روی دیسک media.

بایت‌ها همین‌جا می‌مانند. ردیف contents بعداً با storage_key ساخته می‌شود.
"""

from pathlib import Path
import uuid

MEDIA_ROOT = Path(__file__).resolve().parent.parent / "stt" / "media"

_IMAGE_SUFFIX = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/heic": ".heic",
    "image/heif": ".heif",
}
_FILE_SUFFIX = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "application/zip": ".zip",
    "application/x-zip-compressed": ".zip",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
    "video/ogg": ".ogv",
    "video/3gpp": ".3gp",
}
_SUFFIX_KIND = {}
for _mime, _suffix in _IMAGE_SUFFIX.items():
    _SUFFIX_KIND[_suffix] = ("IMAGE", _mime)
for _mime, _suffix in _FILE_SUFFIX.items():
    _SUFFIX_KIND.setdefault(_suffix, ("FILE", _mime))
_SUFFIX_KIND[".jpg"] = ("IMAGE", "image/jpeg")
_SUFFIX_KIND[".jpeg"] = ("IMAGE", "image/jpeg")


def classify_upload(content_type: str, original_filename: str) -> tuple[str, str, str]:
    """نوع محتوا، MIME تمیز و پسوند را از فایل برمی‌گرداند."""
    mime = (content_type or "").split(";")[0].strip().lower()
    suffix = Path(original_filename or "").suffix.lower()
    if mime in _IMAGE_SUFFIX:
        return "IMAGE", mime, _IMAGE_SUFFIX[mime]
    if mime in _FILE_SUFFIX:
        return "FILE", mime, _FILE_SUFFIX[mime]
    guessed = _SUFFIX_KIND.get(suffix)
    if guessed is None:
        raise ValueError("این نوع فایل پذیرفته نیست. عکس، فیلم یا سند بفرستید")
    return guessed[0], guessed[1], suffix


def store_upload(data: bytes, created_by: int, content_type: str, original_filename: str) -> dict:
    """بایت را می‌نویسد و فیلدهای create_content را برمی‌گرداند."""
    if not data:
        raise ValueError("فایل خالی است")
    kind, mime, suffix = classify_upload(content_type, original_filename)
    folder = "images" if kind == "IMAGE" else "files"
    key = f"{folder}/{created_by}/{uuid.uuid4().hex}{suffix}"
    dest = MEDIA_ROOT / key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    raw_name = Path(original_filename or "").name.strip()
    filename = raw_name or f"upload{suffix}"
    return {
        "content_kind": kind,
        "storage_key": key,
        "original_filename": filename[:255],
        "mime_type": mime,
        "file_size_bytes": len(data),
        "path": dest,
    }
