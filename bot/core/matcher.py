import re
from functools import lru_cache

# Russian noun declension endings
RUSSIAN_ENDINGS = (
    # Singular noun cases
    "а",    # война
    "у",    # путину
    "е",    # войне
    "ы",    # войны
    "и",    # армии
    "о",    # слово
    "ой",   # войной
    "ом",   # путем
    "я",    # дядя
    "ю",    # краю
    "ем",   # полем
    "ью",   # кровью
    # Plural noun cases
    "ов",   # путинов
    "ев",   # краёв
    "ёв",   # бойцёв
    "ей",   # войней
    "ий",   # армий
    "ам",   # войнам
    "ям",   # армиям
    "ами",  # войнами
    "ями",  # армиями
    "ьми",  # детьми
    "ах",   # войнах
    "ях",   # армиях
    # Derived noun suffixes
    "щина",  # путинщина
    "щины",  # путинщины
    "щине",  # путинщине
    "щину",  # путинщину
    "щиной", # путинщиной
    "щин",   # путинщин
    "изм",   # путинизм
    "изма",  # путинизма
    "изму",  # путинизму
    "измом", # путинизмом
    "изме",  # путинизме
    "ист",   # путинист
    "иста",  # путиниста
    "исту",  # путинисту
    "истом", # путинистом
    "исте",  # путинисте
    "исты",  # путинисты
    "истов", # путинистов
    "истам", # путинистам
    "истами",# путинистами
    "истах", # путинистах
    "ость",  # путинность
    "ости",  # путинности
    "остью", # путинностью
    "ность", # путинность
    "ности", # путинности
    "ностью",# путинностью
    "ство",  # путинство
    "ства",  # путинства
    "ству",  # путинству
    "ством", # путинством
    "стве",  # путинстве
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


def find_triggered_keywords(text: str, keywords: list[str]) -> list[str]:
    """Return configured keywords that match the input text."""

    found: list[str] = []
    for keyword in keywords:
        if build_keyword_pattern(keyword).search(text):
            found.append(keyword)
    return found
