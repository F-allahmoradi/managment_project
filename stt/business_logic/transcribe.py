"""تبدیل گفتار به متن.

فایل با ffmpeg در صورت نیاز مونو ۱۶ کیلوهرتز می‌شود.
اگر کلید AvalAI باشد از /audio/transcriptions می‌رود؛
مدل پیش‌فرض gpt-transcribe است چون whisper-1 در آن سرویس قطع شده.
بدون کلید، Google Web Speech استفاده می‌شود.
متن خام گفتار در لاگ نمی‌آید.
"""

from pathlib import Path
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid

from logging_module import logged_step
from paths import STT_ROOT, load_crud_symbol

from errors.crud import (
    ConfigError,
    EmptyTranscriptError,
    InvalidInputError,
    SttProviderError,
    SttTimeoutError,
    SttUnrecognizedError,
)

_QUALITY_ENERGY = {
    "low": 200,
    "medium": 300,
    "high": 450,
}


def _ffmpeg_path() -> str | None:
    """مسیر ffmpeg محلی یا سیستمی را برمی‌گرداند."""
    configured = (os.environ.get("FFMPEG_PATH") or "").strip()
    if configured and Path(configured).is_file():
        return configured
    local_win = STT_ROOT.parent / "ffmpeg.exe"
    if local_win.exists():
        return str(local_win)
    bundled_win = STT_ROOT / "ffmpeg.exe"
    if bundled_win.exists():
        return str(bundled_win)
    bundled = STT_ROOT / "ffmpeg"
    if bundled.exists():
        return str(bundled)
    return shutil.which("ffmpeg")


def _configure_pydub() -> str:
    """مبدل pydub را روی ffmpeg می‌گذارد."""
    converter = _ffmpeg_path()
    if not converter:
        raise ConfigError("ffmpeg برای تبدیل فایل صوتی پیدا نشد")
    from pydub import AudioSegment

    AudioSegment.converter = converter
    return converter


def downsample_command(converter: str, src: str, dest: str) -> list[str]:
    """دستور ffmpeg برای WAV مونو ۱۶ کیلوهرتز مناسب گوگل."""
    return [
        converter,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        src,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        dest,
    ]


def _wav_for_google(src: Path) -> str:
    """فایل ورودی را به WAV سبک تبدیل می‌کند."""
    converter = _ffmpeg_path()
    if not converter:
        raise ConfigError("ffmpeg برای تبدیل فایل صوتی پیدا نشد")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        wav_path = tmp_wav.name
    command = downsample_command(converter, str(src), wav_path)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=45,
        )
    except subprocess.TimeoutExpired as exc:
        Path(wav_path).unlink(missing_ok=True)
        raise SttProviderError("تبدیل فایل صوتی بیش از حد طول کشید") from exc
    if completed.returncode != 0 or not Path(wav_path).is_file():
        Path(wav_path).unlink(missing_ok=True)
        raise SttProviderError("پردازش فایل صوتی شکست خورد")
    return wav_path


def _cloud_key() -> str:
    """کلید همان سرویس مدل زبانی سرور است."""
    return (
        os.environ.get("NLP_LLM_API_KEY")
        or os.environ.get("AVALAI_API_KEY")
        or ""
    ).strip()


_AVALAI_FILES = {
    ".flac",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".m4a",
    ".aac",
    ".ogg",
    ".wav",
    ".webm",
}

_STT_MODELS = (
    "gpt-transcribe",
    "gpt-4o-mini-transcribe",
    "groq.whisper-large-v3-turbo",
    "whisper-1",
)


def _stt_models() -> list[str]:
    """مدل تنظیم‌شده را اول می‌گذارد؛ بقیه فقط اگر آن یکی قطع باشد."""
    preferred = (os.environ.get("STT_MODEL") or "gpt-transcribe").strip()
    ordered: list[str] = []
    for name in [preferred, *_STT_MODELS]:
        if name and name not in ordered:
            ordered.append(name)
    return ordered


def _recognize_google(audio_data, language: str) -> str:
    """صدا را با Google Web Speech به متن تبدیل می‌کند."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    recognizer.operation_timeout = 25
    try:
        text = recognizer.recognize_google(audio_data, language=language)
    except sr.UnknownValueError as exc:
        raise SttUnrecognizedError("صحبت تشخیص داده نشد") from exc
    except sr.WaitTimeoutError as exc:
        raise SttTimeoutError("زمان پاسخ سرویس تبدیل صدا تمام شد") from exc
    except sr.RequestError as exc:
        raise SttProviderError("ارتباط با سرویس تبدیل صدا برقرار نشد") from exc
    except (TimeoutError, subprocess.TimeoutExpired) as exc:
        raise SttTimeoutError("زمان پاسخ سرویس تبدیل صدا تمام شد") from exc
    cleaned = (text or "").strip()
    if not cleaned:
        raise EmptyTranscriptError("متن استخراج‌شده خالی است")
    return cleaned


def _recognize_avalai(file_path: str, language: str, model: str) -> str:
    """فایل را با مسیر OpenAI-سازگار AvalAI به متن تبدیل می‌کند."""
    key = _cloud_key()
    if not key:
        raise SttProviderError("کلید تبدیل صدا روی سرور نیست")
    base = (
        os.environ.get("AVALAI_BASE_URL") or "https://api.avalai.ir/v1"
    ).strip().rstrip("/")
    path = Path(file_path)
    suffix = path.suffix.lower() or ".wav"
    mime = {
        ".wav": "audio/wav",
        ".webm": "audio/webm",
        ".ogg": "audio/ogg",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".aac": "audio/aac",
        ".flac": "audio/flac",
    }.get(suffix, "application/octet-stream")
    lang = (language or "fa").split("-", 1)[0]
    boundary = "----mgmtstt" + uuid.uuid4().hex

    def field(name: str, value: str) -> list[bytes]:
        return [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
            value.encode("utf-8"),
            b"\r\n",
        ]

    parts: list[bytes] = []
    parts.extend(field("model", model))
    if "whisper" in model.lower():
        parts.extend(field("language", lang))
    parts.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                'Content-Disposition: form-data; name="file"; '
                f'filename="speech{suffix}"\r\n'
                f"Content-Type: {mime}\r\n\r\n"
            ).encode("utf-8"),
            path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    request = urllib.request.Request(
        base + "/audio/transcriptions",
        data=b"".join(parts),
        method="POST",
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        },
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=45, context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except TimeoutError as exc:
        raise SttTimeoutError("زمان پاسخ سرویس تبدیل صدا تمام شد") from exc
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise SttProviderError("کلید تبدیل صدا روی این سرور پذیرفته نشد") from exc
        if exc.code in {404, 410}:
            raise SttProviderError("مدل تبدیل صدا روی این حساب فعال نیست") from exc
        raise SttProviderError("سرویس تبدیل صدا پاسخ نامعتبر داد") from exc
    except urllib.error.URLError as exc:
        raise SttProviderError("ارتباط با سرویس تبدیل صدا برقرار نشد") from exc
    text = ""
    if isinstance(payload, dict):
        text = str(payload.get("text") or "").strip()
    if not text:
        raise SttUnrecognizedError("صحبت تشخیص داده نشد")
    return text


def _cloud_file(src: Path) -> str:
    """فرمت‌های پذیرفتهٔ AvalAI را همان‌طور می‌فرستد؛ بقیه WAV می‌شوند."""
    if src.suffix.lower() in _AVALAI_FILES:
        return str(src)
    return _wav_for_google(src)


def _recognize_cloud(file_path: str, language: str) -> str:
    """مدل تنظیم‌شده را می‌زند؛ اگر قطع باشد مدل بعدی همان سرویس."""
    last_error: Exception | None = None
    for model in _stt_models():
        try:
            return _recognize_avalai(file_path, language, model)
        except (SttUnrecognizedError, EmptyTranscriptError, SttTimeoutError):
            raise
        except SttProviderError as exc:
            if "پذیرفته نشد" in str(exc):
                raise
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise SttProviderError("سرویس تبدیل صدا پاسخ نامعتبر داد")


def _recognize_google_file(wav_path: str, language: str) -> str:
    """WAV را با Google Web Speech می‌خواند."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
    return _recognize_google(audio_data, language)


@logged_step("transcribe")
def transcribe_file(file_path: str, language: str = "fa-IR") -> str:
    """فایل صوتی را به wav سبک تبدیل می‌کند و متن فارسی برمی‌گرداند."""
    path = Path(file_path).expanduser()
    if not path.is_file():
        raise InvalidInputError("فایل صوتی پیدا نشد")
    wav_path = None
    try:
        if _cloud_key():
            cloud_path = _cloud_file(path)
            if cloud_path != str(path):
                wav_path = cloud_path
            return _recognize_cloud(cloud_path, language)
        wav_path = _wav_for_google(path)
        return _recognize_google_file(wav_path, language)
    except (
        InvalidInputError,
        EmptyTranscriptError,
        SttUnrecognizedError,
        SttProviderError,
        SttTimeoutError,
        ConfigError,
    ):
        raise
    except Exception as exc:
        raise SttProviderError("پردازش فایل صوتی شکست خورد") from exc
    finally:
        if wav_path:
            Path(wav_path).unlink(missing_ok=True)


@logged_step("listen")
def listen_and_transcribe(
    language: str = "fa-IR",
    timeout: int = 5,
    phrase_time_limit: int = 10,
    quality: str = "medium",
) -> str:
    """از میکروفون همین ماشین ضبط می‌کند و متن برمی‌گرداند."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = _QUALITY_ENERGY.get(quality, 300)
    recognizer.pause_threshold = 0.8
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio_data = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
            )
    except sr.WaitTimeoutError as exc:
        raise SttTimeoutError("زمان انتظار شروع صحبت تمام شد") from exc
    except OSError as exc:
        raise ConfigError("میکروفون در دسترس نیست") from exc
    return _recognize_google(audio_data, language)


@logged_step("insert")
def save_transcript_text(text: str, created_by: int) -> int:
    """متن رونویسی را به‌صورت محتوای TEXT در contents می‌نویسد."""
    insert_content = load_crud_symbol("services.content", "insert_content")
    return insert_content(
        {"content_kind": "TEXT", "text_body": text},
        created_by=created_by,
    )


@logged_step("insert")
def save_voice_and_transcript(
    text: str,
    audio_bytes: bytes,
    created_by: int,
    mime_type: str,
    original_filename: str | None = None,
) -> int:
    """فایل صوت را روی دیسک می‌گذارد و یک ردیف VOICE با متن caption می‌سازد."""
    from business_logic.store import store_audio_bytes

    insert_content = load_crud_symbol("services.content", "insert_content")
    media = store_audio_bytes(
        audio_bytes,
        created_by,
        mime_type,
        original_filename,
    )
    return insert_content(
        {
            "content_kind": "VOICE",
            "text_body": text,
            **media,
        },
        created_by=created_by,
    )


@logged_step("insert")
def save_voice_from_path(
    text: str,
    file_path: str,
    created_by: int,
    mime_type: str | None = None,
    original_filename: str | None = None,
) -> int:
    """فایل صوتی محلی را کپی می‌کند و VOICE به‌همراه متن ذخیره می‌کند."""
    path = Path(file_path).expanduser()
    if not path.is_file():
        raise InvalidInputError("فایل صوتی پیدا نشد")
    data = path.read_bytes()
    name = original_filename or path.name
    mime = mime_type or {
        ".webm": "audio/webm",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".3gp": "audio/3gpp",
        ".amr": "audio/amr",
    }.get(path.suffix.lower(), "application/octet-stream")
    return save_voice_and_transcript(
        text,
        data,
        created_by,
        mime,
        name,
    )


@logged_step("delete")
def delete_transcript_content(content_id: int, actor_id: int) -> int:
    """متن یا صوت ذخیره‌شده را نرم‌حذف می‌کند."""
    delete_content = load_crud_symbol("services.content", "delete_content")
    return delete_content(content_id, actor_id=actor_id)
