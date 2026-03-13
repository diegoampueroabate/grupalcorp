"""Handle Telegram media downloads and processing."""

import base64
import logging
import os
import tempfile

import httpx

logger = logging.getLogger(__name__)


async def download_telegram_photo(photo, bot) -> str:
    """Download a Telegram photo to a temp file and return the path."""
    file = await bot.get_file(photo.file_id)
    fd, temp_path = tempfile.mkstemp(suffix=".jpg", prefix="meta_ad_")
    os.close(fd)
    await file.download_to_drive(temp_path)
    return temp_path


async def download_telegram_voice(voice, bot) -> str:
    """Download a Telegram voice message to a temp OGG file and return the path."""
    file = await bot.get_file(voice.file_id)
    fd, temp_path = tempfile.mkstemp(suffix=".ogg", prefix="voice_")
    os.close(fd)
    await file.download_to_drive(temp_path)
    return temp_path


async def transcribe_audio(file_path: str, openai_api_key: str) -> str:
    """Transcribe an audio file using OpenAI Whisper API."""
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {openai_api_key}"},
                files={"file": ("voice.ogg", f, "audio/ogg")},
                data={"model": "whisper-1"},
                timeout=30.0,
            )
    response.raise_for_status()
    return response.json()["text"]


def encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """Read an image file and return (base64_data, media_type)."""
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/jpeg")
    return data, media_type
