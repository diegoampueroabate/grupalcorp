"""Telegram message formatting utilities."""

TELEGRAM_MAX_LENGTH = 4096


def chunk_message(text: str, max_length: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    """Split long text into Telegram-safe chunks, breaking at newlines."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_length:
            if current:
                chunks.append(current)
            # Handle single lines exceeding limit
            while len(line) > max_length:
                chunks.append(line[:max_length])
                line = line[max_length:]
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        chunks.append(current)
    return chunks or [text[:max_length]]
