import re
from functools import lru_cache

# Common Russian endings for a simple deterministic first pass.
RUSSIAN_ENDINGS = (
    "а",
    "я",
    "у",
    "ю",
    "е",
    "и",
    "ы",
    "о",
    "ой",
    "ей",
    "ом",
    "ем",
    "ах",
    "ях",
    "ам",
    "ям",
    "ых",
    "их",
    "ть",
    "л",
    "ла",
    "ли",
    "ло",
    "ет",
    "ют",
    "ит",
    "ат",
    "ят",
)

_WORD_CHARS = r"0-9A-Za-zА-Яа-яЁё_"


def _is_word_keyword(keyword: str) -> bool:
    """Return True when keyword contains only word characters."""

    return re.fullmatch(rf"[{_WORD_CHARS}]+", keyword) is not None


def _build_variants(keyword: str) -> list[str]:
    """Build base and suffix variants for a normalized keyword."""

    normalized = keyword.strip().lower()
    if not normalized:
        return []

    variants = {normalized}
    # Short words are left as exact-only to reduce noisy matches.
    if len(normalized) >= 4 and _is_word_keyword(normalized):
        for ending in RUSSIAN_ENDINGS:
            variants.add(f"{normalized}{ending}")

    return sorted(variants, key=len, reverse=True)


@lru_cache(maxsize=2048)
def build_keyword_pattern(keyword: str) -> re.Pattern[str]:
    """Compile a cached regex pattern for keyword variants."""

    variants = _build_variants(keyword)
    if not variants:
        return re.compile(r"a^", re.IGNORECASE)

    escaped = "|".join(re.escape(item) for item in variants)
    if _is_word_keyword(keyword.strip().lower()):
        return re.compile(
            rf"(?<![{_WORD_CHARS}])(?:{escaped})(?![{_WORD_CHARS}])",
            re.IGNORECASE,
        )
    return re.compile(escaped, re.IGNORECASE)


def find_triggered_keywords(text: str, keywords: list[str]) -> set[str]:
    """Return configured keywords that match the input text."""

    found: set[str] = set()
    for keyword in keywords:
        if build_keyword_pattern(keyword).search(text):
            found.add(keyword)
    return found
