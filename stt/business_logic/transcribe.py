"""تبدیل گفتار به متن با Google Web Speech API.

همان موتور پروژه ایجنت وقایع است: speech_recognition + ffmpeg.
فایل قبل از ارسال به گوگل مونو ۱۶ کیلوهرتز می‌شود تا حجم و زمان کمتر شود.
ffmpeg روی لینوکس از PATH خوانده می‌شود؛ ffmpeg.exe محلی هم پذیرفته است.
متن خام گفتار در لاگ نمی‌آید.
"""

from pathlib import Path
import shutil
import subprocess
import tempfile

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
    local_win = STT_ROOT.parent / "ffmpeg.exe"
    if local_win.exists():
        return str(local_win)
    bundled = STT_ROOT / "ffmpeg.exe"
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


def _recognize(audio_data, language: str) -> str:
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


@logged_step("transcribe")
def transcribe_file(file_path: str, language: str = "fa-IR") -> str:
    """فایل صوتی را به wav سبک تبدیل می‌کند و متن فارسی برمی‌گرداند."""
    import speech_recognition as sr

    path = Path(file_path).expanduser()
    if not path.is_file():
        raise InvalidInputError("فایل صوتی پیدا نشد")
    wav_path = None
    try:
        wav_path = _wav_for_google(path)
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        return _recognize(audio_data, language)
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
    return _recognize(audio_data, language)


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
