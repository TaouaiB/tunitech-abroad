import re


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,5}\d{2,4}(?!\w)"
)
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)


def mask_sensitive_data(text: str) -> str:
    """
    Removes common direct identifiers before CV text is sent to an LLM provider.
    """
    masked = EMAIL_RE.sub("[email redacted]", text)
    masked = PHONE_RE.sub("[phone redacted]", masked)
    return URL_RE.sub("[url redacted]", masked)
