from .matcher import build_keyword_pattern


def mask_word(word: str, mask_char: str) -> str:
    """Mask a word: first and last chars visible, middle chars alternate masked/visible."""

    if len(word) <= 1:
        return word

    chars = []
    for i, ch in enumerate(word):
        if i == 0 or i == len(word) - 1:
            chars.append(ch)
        elif i % 2 == 1:
            chars.append(mask_char)
        else:
            chars.append(ch)
    return "".join(chars)


def censor_text(text: str, triggered_keywords: list[str], mask_char: str) -> str:
    """Replace matched keyword variants in text with masked forms."""

    result = text
    for keyword in sorted(triggered_keywords, key=len, reverse=True):
        pattern = build_keyword_pattern(keyword)
        # Mask each concrete match so endings are masked too.
        result = pattern.sub(lambda match: mask_word(match.group(0), mask_char=mask_char), result)
    return result
