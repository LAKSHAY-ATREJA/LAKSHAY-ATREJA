def citation_coverage(answer: str, source_ids: list[str]) -> float:
    if not source_ids:
        return 0.0
    cited = sum(1 for s in source_ids if f"[{s}]" in answer)
    return cited / len(source_ids)


def grounded_token_ratio(answer: str, contexts: list[str]) -> float:
    words = [w.strip(".,:;!?()[]").lower() for w in answer.split() if len(w) > 3]
    if not words:
        return 1.0
    vocab = set(" ".join(contexts).lower().split())
    return sum(w in vocab for w in words) / len(words)
