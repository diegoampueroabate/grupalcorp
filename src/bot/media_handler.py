"""Handle Telegram photo downloads for use as ad creatives."""

import os
import tempfile


async def download_telegram_photo(photo, bot) -> str:
    """Download a Telegram photo to a temp file and return the path."""
    file = await bot.get_file(photo.file_id)
    fd, temp_path = tempfile.mkstemp(suffix=".jpg", prefix="meta_ad_")
    os.close(fd)
    await file.download_to_drive(temp_path)
    return temp_path
