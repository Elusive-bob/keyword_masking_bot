def validate_word(text: str) -> bool:
    """Return True when text is a single word made of letters or digits."""

    if not text or any(char.isspace() for char in text):
        return False
    return all(char.isalnum() for char in text)


def validate_mask_char(text: str) -> bool:
    """Return True when text is exactly one non-space symbol."""

    return len(text) == 1 and not text.isspace()
