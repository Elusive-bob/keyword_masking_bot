import json
from dataclasses import dataclass


@dataclass
class BootstrapConfig:
    """Startup configuration loaded from config.json."""

    token: str
    default_keywords: list[str]
    db_path: str
    mask_char: str


def load_bootstrap_config(path: str) -> BootstrapConfig:
    """Load, validate, and normalize bootstrap config values from JSON."""

    with open(path, "r", encoding="utf-8") as file:
        raw = json.load(file)

    token = str(raw.get("token", "")).strip()
    if not token:
        raise ValueError("'token' is required in config.json")

    db_path = str(raw.get("db_path", "bot.db")).strip() or "bot.db"
    mask_char = str(raw.get("mask_char", "●")).strip() or "●"
    mask_char = mask_char[0]

    raw_keywords = raw.get("default_keywords", [])
    if not isinstance(raw_keywords, list):
        raise ValueError("'default_keywords' must be a list in config.json")

    seen: set[str] = set()
    default_keywords: list[str] = []
    for item in raw_keywords:
        if not isinstance(item, str):
            continue
        normalized = item.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            default_keywords.append(normalized)

    return BootstrapConfig(
        token=token,
        default_keywords=default_keywords,
        db_path=db_path,
        mask_char=mask_char,
    )
