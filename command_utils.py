from typing import Tuple


def parse_command(text: str) -> Tuple[str, str]:
    raw = (text or "").strip()
    if not raw.startswith("/"):
        return "", ""
    parts = raw.split(" ", 1)
    cmd = parts[0]
    args = parts[1].strip() if len(parts) > 1 else ""
    return cmd, args
