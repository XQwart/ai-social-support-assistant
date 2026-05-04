def shorten_inline(text: str, limit: int) -> str:
    text = (text).strip().replace("\r\n", "\n")
    if len(text) <= limit:
        return text
    cut = text.rfind(" ", 0, limit)
    if cut < limit // 2:
        cut = limit
    return text[:cut].rstrip(" ,.;:—-") + "…"


def shorten_block(text: str, limit: int) -> str:
    text = (text).strip().replace("\r\n", "\n")
    if len(text) <= limit:
        return text
    cut = text.rfind("\n\n", 0, limit)
    if cut < limit // 2:
        cut = text.rfind(" ", 0, limit)
    if cut < limit // 2:
        cut = limit
    return text[:cut].rstrip(" ,.;:—-") + "\n\n…"
