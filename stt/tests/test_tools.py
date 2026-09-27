"""ثبت ابزار STT و ذخیره متن روی PostgreSQL با موتور جعلی."""

from pathlib import Path
import asyncio
import sys
import tempfile
import unittest
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from paths import ensure_import_path

ensure_import_path()

from errors.crud import CONTENT_NOT_FOUND, INVALID_INPUT, STT_UNRECOGNIZED
from mcp_server.metadata import (
    SERVER_NAME,
    TITLE_RECORD_AUDIO_TO_TEXT,
    TITLE_SAVE_TRANSCRIPT,
    TITLE_TRANSCRIBE_AUDIO,
)
from mcp_server.tools.delete_transcript import run_delete_transcript
from mcp_server.tools.save_transcript import run_save_transcript
from mcp_server.tools.transcribe_audio import run_transcribe_audio
from services.content import fetch_content
from tests.conftest import bind_actor_as_role


class ServerPlumbingTests(unittest.TestCase):
    """ثبت ابزار تبدیل گفتار را بررسی می‌کند."""

    def test_metadata_names_management_stt(self) -> None:
        from mcp_server.server import mcp

        self.assertEqual(SERVER_NAME, "management-stt")
        tools = asyncio.run(mcp.list_tools())
        by_name = {tool.name: tool for tool in tools}
        self.assertEqual(
            set(by_name),
            {"transcribe_audio", "record_audio_to_text", "save_transcript", "delete_transcript"},
        )
        self.assertEqual(by_name["transcribe_audio"].title, TITLE_TRANSCRIBE_AUDIO)
        self.assertTrue(by_name["transcribe_audio"].annotations.read_only_hint)
        self.assertEqual(by_name["record_audio_to_text"].title, TITLE_RECORD_AUDIO_TO_TEXT)
        self.assertFalse(by_name["record_audio_to_text"].annotations.read_only_hint)
        self.assertEqual(by_name["save_transcript"].title, TITLE_SAVE_TRANSCRIPT)


class DownsampleCommandTests(unittest.TestCase):
    """فایل قبل از گوگل مونو ۱۶ کیلوهرتز می‌شود."""

    def test_command_is_16k_mono(self) -> None:
        from business_logic.transcribe import downsample_command

        command = downsample_command("/usr/bin/ffmpeg", "/tmp/in.webm", "/tmp/out.wav")
        self.assertEqual(command[command.index("-ac") + 1], "1")
        self.assertEqual(command[command.index("-ar") + 1], "16000")
        self.assertIn("pcm_s16le", command)


class TranscribeToolTests(unittest.TestCase):
    """رونویسی فایل با Google جعلی."""

    def test_missing_file_is_invalid(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            result = run_transcribe_audio(file_path="/tmp/does-not-exist-stt.webm")
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["error_code"], INVALID_INPUT)
        finally:
            ali.close()

    def test_transcribe_file_returns_persian_text(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(b"RIFF")
                path = tmp.name
            with patch(
                "mcp_server.tools.transcribe_audio.transcribe_file",
                return_value="گزارش پیشرفت پروژه آماده است",
            ):
                result = run_transcribe_audio(file_path=path, language="fa-IR")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["transcribed_text"], "گزارش پیشرفت پروژه آماده است")
            self.assertEqual(result["language"], "fa-IR")
        finally:
            Path(path).unlink(missing_ok=True)
            ali.close()

    def test_unrecognized_speech_is_mapped(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(b"RIFF")
                path = tmp.name
            from errors.crud import SttUnrecognizedError

            with patch(
                "mcp_server.tools.transcribe_audio.transcribe_file",
                side_effect=SttUnrecognizedError("صحبت تشخیص داده نشد"),
            ):
                result = run_transcribe_audio(file_path=path)
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["error_code"], STT_UNRECOGNIZED)
        finally:
            Path(path).unlink(missing_ok=True)
            ali.close()


class SaveTranscriptTests(unittest.TestCase):
    """ذخیره متن رونویسی در contents."""

    def test_save_transcript_writes_text_content(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        audio_path = None
        try:
            saved = run_save_transcript(text="یادداشت صوتی جلسه امروز")
            self.assertEqual(saved["status"], "success")
            loaded = fetch_content(saved["id"])
            self.assertEqual(loaded["content_kind_code"], "TEXT")
            self.assertEqual(loaded["text_body"], "یادداشت صوتی جلسه امروز")
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(b"webm-audio-bytes")
                audio_path = tmp.name
            voiced = run_save_transcript(
                text="گزارش صوتی آزمایشی",
                file_path=audio_path,
                mime_type="audio/webm",
                original_filename="note.webm",
            )
            self.assertEqual(voiced["status"], "success")
            self.assertEqual(voiced["content_kind"], "VOICE")
            audio_row = fetch_content(voiced["id"])
            self.assertEqual(audio_row["content_kind_code"], "VOICE")
            self.assertEqual(audio_row["text_body"], "گزارش صوتی آزمایشی")
            self.assertEqual(audio_row["original_filename"], "note.webm")
            self.assertTrue(audio_row["storage_key"])
            removed = run_delete_transcript(id=saved["id"])
            self.assertEqual(removed["status"], "success")
            gone = run_delete_transcript(id=saved["id"])
            self.assertEqual(gone["status"], "error")
            self.assertEqual(gone["error_code"], CONTENT_NOT_FOUND)
            run_delete_transcript(id=voiced["id"])
        finally:
            if audio_path:
                Path(audio_path).unlink(missing_ok=True)
            ali.close()

    def test_blank_transcript_is_invalid(self) -> None:
        ali = bind_actor_as_role("مدیر پروژه")
        try:
            result = run_save_transcript(text="   ")
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["error_code"], INVALID_INPUT)
        finally:
            ali.close()


if __name__ == "__main__":
    unittest.main()
