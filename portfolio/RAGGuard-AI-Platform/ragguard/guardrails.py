import re

PII = [re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), re.compile(r"\b(?:\d[ -]*?){13,16}\b")]
INJECTION = ("ignore previous", "system prompt", "developer message", "reveal your instructions")


def inspect_prompt(text: str) -> list[str]:
    flags = []
    low = text.lower()
    if any(x in low for x in INJECTION):
        flags.append("prompt_injection")
    if any(p.search(text) for p in PII):
        flags.append("sensitive_identifier")
    return flags
