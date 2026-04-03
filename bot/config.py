import json
from dataclasses import dataclass



@dataclass
class BootstrapConfig:
    """Startup configuration loaded from config.json."""

    token: str
    default_keywords: list[str]
    db_path: str
    default_mask_char: str


def load_bootstrap_config(path: str) -> BootstrapConfig:
    """Load, validate, and normalize bootstrap config values from JSON."""

    with open(path, "r", encoding="utf-8") as file:
        raw = json.load(file)

    token = raw.get("token")
    if not token:
        raise ValueError("Missing or empty 'token' in config.json")
    
    db_path = raw.get("db_path")
    if not db_path:
        raise ValueError("Missing or empty 'db_path' in config.json")
    
    default_mask_char = raw.get("default_mask_char")
    if not default_mask_char or len(default_mask_char) != 1:
        raise ValueError("Missing 'default_mask_char' or not exactly one character in config.json")
    
    raw_default_keywords = raw.get("default_keywords")
    if not isinstance(raw_default_keywords, list) or not raw_default_keywords:
        raise ValueError("Invalid 'default_keywords' in config.json")

    default_keywords = [keyword.strip().lower() for keyword in raw_default_keywords if isinstance(keyword, str)]
    if len(default_keywords) != len(raw_default_keywords) or not all(default_keywords):
        raise ValueError("Invalid 'default_keywords' in config.json")

    return BootstrapConfig(
        token=token,
        default_keywords=default_keywords,
        db_path=db_path,
        default_mask_char=default_mask_char,
    )
