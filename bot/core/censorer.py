from .matcher import build_keyword_pattern


def mask_word(word: str, mask_char: str = "●") -> str:
    """Mask a word while preserving readable prefix and suffix."""

    if len(word) <= 2:
        return word

    # Longer words keep more visible characters at both ends so users can infer them.
    length = len(word)
    if length <= 4:
        visible = 1
    elif length <= 6:
        visible = 2
    else:
        visible = 3
    


    masked_length = max(1, length - (visible * 2))
    prefix = word[:visible]
    suffix = word[-visible:]
    return f"{prefix}{mask_char * masked_length}{suffix}"


def censor_text(text: str, triggered_keywords: set[str], mask_char: str = "●") -> str:
    """Replace matched keyword variants in text with masked forms."""

    result = text
    for keyword in sorted(triggered_keywords, key=len, reverse=True):
        pattern = build_keyword_pattern(keyword)
        # Mask each concrete match so endings are masked too.
        result = pattern.sub(lambda match: mask_word(match.group(0), mask_char=mask_char), result)
    return result
