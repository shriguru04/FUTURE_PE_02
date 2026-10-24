"""Deterministic claim/avoid-term checks that run AFTER the LLM, so we never rely on the model grading itself.
Pure Python (no third-party imports)."""
import re


def iter_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from iter_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from iter_strings(v)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()


def matches_supported(claim: str, supported: list[str]) -> bool:
    c = _norm(claim)
    if not c:
        return False
    for s in supported:
        n = _norm(s)
        if n and (n in c or c in n):
            return True
    return False


def review_claims(items: list[dict], supported_claims: list[str], avoid_terms: list[str], sections: dict) -> list[dict]:
    out = []
    for it in items:
        it = dict(it)
        if it.get("status") == "supported" and not matches_supported(it.get("claim", ""), supported_claims):
            it["status"] = "needs_verification"
            it["note"] = (it.get("note", "") + " Downgraded: not found in the product's supported claims.").strip()
        out.append(it)
    # Avoid-terms are scanned in everything except the review itself.
    haystack = "\n".join(s for k, v in sections.items() if k != "claims_review" for s in iter_strings(v))
    for term in avoid_terms:
        t = term.strip()
        if t and re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", haystack, re.IGNORECASE):
            out.append({"claim": f'Contains avoided term "{t}"', "status": "unsupported",
                        "note": "Your brand settings say to avoid this word or claim."})
    return out
