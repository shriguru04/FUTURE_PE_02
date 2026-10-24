"""Pure analytics math. No third-party imports so it is trivially testable.
Missing data yields None (never a misleading 0)."""

FIELDS = ("impressions", "reach", "video_views", "clicks", "conversions", "spend", "revenue")


def _num(v):
    return None if v is None else float(v)


def safe_div(n, d):
    n, d = _num(n), _num(d)
    if n is None or d is None or d == 0:
        return None
    return n / d


def _pct(n, d):
    r = safe_div(n, d)
    return None if r is None else round(r * 100, 4)


def _r(v):
    return None if v is None else round(v, 4)


def compute_rates(m: dict) -> dict:
    return {
        "ctr": _pct(m.get("clicks"), m.get("impressions")),              # clicks / impressions * 100
        "conversion_rate": _pct(m.get("conversions"), m.get("clicks")),  # conversions / clicks * 100
        "cpc": _r(safe_div(m.get("spend"), m.get("clicks"))),            # spend / clicks
        "cpa": _r(safe_div(m.get("spend"), m.get("conversions"))),       # spend / conversions
        "roas": _r(safe_div(m.get("revenue"), m.get("spend"))),          # revenue / spend
    }


def aggregate(rows: list[dict]) -> dict:
    """Sum each field over rows that have a value. A field with no values at all stays None."""
    totals = {}
    for f in FIELDS:
        vals = [_num(r.get(f)) for r in rows if r.get(f) is not None]
        totals[f] = sum(vals) if vals else None
    return totals


def summarize(rows: list[dict]) -> dict:
    totals = aggregate(rows)
    return {"totals": totals, "rates": compute_rates(totals), "row_count": len(rows)}
