"""Pure helpers for pulling a JSON object out of raw LLM text. No third-party imports."""
import json
import re

_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


def extract_json(text: str):
    """Parse model output as JSON. Tolerates a code fence or prose around ONE top-level object.
    Raises ValueError if no valid JSON object/array can be recovered."""
    if text is None:
        raise ValueError("empty response")
    s = text.strip()
    m = _FENCE.match(s)
    if m:
        s = m.group(1).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    start = min((i for i in (s.find("{"), s.find("[")) if i != -1), default=-1)
    if start == -1:
        raise ValueError("response contains no JSON")
    try:
        obj, _ = json.JSONDecoder().raw_decode(s[start:])
        return obj
    except json.JSONDecodeError as exc:
        raise ValueError(f"response is not valid JSON: {exc.msg}") from exc


def normalize_hashtags(tags: list[str]) -> list[str]:
    seen, out = set(), []
    for t in tags:
        t = re.sub(r"\s+", "", str(t)).lstrip("#")
        t = re.sub(r"[^\w]", "", t, flags=re.UNICODE)
        if not t or t.lower() in seen:
            continue
        seen.add(t.lower())
        out.append("#" + t)
    return out
