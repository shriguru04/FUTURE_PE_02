"""Backend export renderers. Operate on a plain dict bundle (no DB access) so they are easy to test.
All formats share one block model: [(kind, text)] with kind in h1,h2,h3,p,li."""
import json
import re
from io import BytesIO
from xml.sax.saxutils import escape

SECTION_TITLES = {
    "summary": "Campaign summary", "hooks": "Hooks", "primary_script": "Primary video script",
    "alt_scripts": "Alternative scripts", "caption": "Caption and description", "ctas": "Calls to action",
    "hashtags": "Hashtags", "variations": "Creative variations for testing",
    "adaptation": "Platform adaptation", "claims_review": "Factual-claims review",
}
SECTION_ORDER = list(SECTION_TITLES)
DISCLAIMER = ("AI-generated draft. Creative suggestions are NOT verified product facts. Review every claim, "
              "check the platform's current ad policies, and never present fictional scripts as real customer experiences.")


def slugify(text: str, default: str = "campaign") -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:60] or default


def _script_blocks(s: dict, level: str = "h3") -> list:
    b = [(level, f"{s.get('title', 'Script')} ({s.get('total_duration_seconds', '?')}s)")]
    for sc in s.get("scenes", []):
        b.append(("p", f"Scene {sc.get('scene_number')} ({sc.get('duration_seconds')}s)"))
        for label, key in (("Visual", "visual_direction"), ("Dialogue", "dialogue"), ("On-screen text", "on_screen_text"),
                           ("Transition", "transition"), ("Audio", "audio_direction")):
            if sc.get(key):
                b.append(("li", f"{label}: {sc[key]}"))
    if s.get("voice_over"):
        b.append(("p", f"Voice-over: {s['voice_over']}"))
    return b


def section_blocks(section: str, p: dict) -> list:
    if section in ("summary", "caption"):
        return [("p", p.get("text", ""))]
    if section in ("hooks", "hashtags", "variations"):
        return [("li", x) for x in p.get("items", [])]
    if section == "primary_script":
        return _script_blocks(p)
    if section == "alt_scripts":
        return [blk for s in p.get("items", []) for blk in _script_blocks(s)]
    if section == "ctas":
        return [("li", f"Primary: {p.get('primary', '')}")] + [("li", f"Alternative: {a}") for a in p.get("alternatives", [])]
    if section == "adaptation":
        return [("li", f"{k.replace('_', ' ').capitalize()}: {v}") for k, v in p.items() if v not in ("", None)]
    if section == "claims_review":
        return [("li", f"[{c.get('status')}] {c.get('claim')}" + (f" - {c['note']}" if c.get("note") else ""))
                for c in p.get("items", [])]
    return [("p", json.dumps(p))]


def to_blocks(bundle: dict) -> list:
    c, brand, product = bundle["campaign"], bundle.get("brand") or {}, bundle.get("product")
    blocks = [("h1", c.get("name", "Campaign")), ("p", DISCLAIMER)]
    blocks += [("h2", "Campaign details")]
    for label, val in (("Status", c.get("status")), ("Platform", c.get("platform")), ("Objective", c.get("objective")),
                       ("Notes", c.get("notes")), ("Exported at", bundle.get("exported_at"))):
        if val:
            blocks.append(("li", f"{label}: {val}"))
    blocks.append(("h2", "Brand context (user-provided)"))
    for label, key in (("Brand", "name"), ("Category", "category"), ("Voice", "voice"), ("Target audience", "target_audience")):
        if brand.get(key):
            blocks.append(("li", f"{label}: {brand[key]}"))
    if product:
        blocks.append(("h2", "Product context (user-provided)"))
        for label, key in (("Product", "name"), ("Description", "description"), ("Offer", "offer_details")):
            if product.get(key):
                blocks.append(("li", f"{label}: {product[key]}"))
        for label, key in (("Supported claims", "supported_claims"), ("Known limitations", "limitations")):
            v = product.get(key)
            if v:
                blocks.append(("li", f"{label}: {', '.join(v) if isinstance(v, list) else v}"))
    for platform, sections in bundle.get("platforms", {}).items():
        blocks.append(("h2", f"Platform version: {platform.replace('_', ' ').title()}"))
        for sec in SECTION_ORDER:
            if sec in sections:
                blocks.append(("h3", SECTION_TITLES[sec]))
                blocks += section_blocks(sec, sections[sec])
    blocks.append(("h2", "Pre-publication review checklist"))
    blocks += [("li", f"[ ] {item}") for item in bundle.get("checklist", [])]
    return blocks


def to_txt(bundle: dict) -> bytes:
    out = []
    for kind, text in to_blocks(bundle):
        if kind == "h1":
            out += [text.upper(), "=" * len(text), ""]
        elif kind == "h2":
            out += ["", text, "-" * len(text)]
        elif kind == "h3":
            out += ["", f"## {text}"]
        elif kind == "li":
            out.append(f"  * {text}")
        else:
            out.append(text)
    return ("\n".join(out) + "\n").encode("utf-8")


def to_markdown(bundle: dict) -> bytes:
    prefix = {"h1": "# ", "h2": "## ", "h3": "### ", "li": "- ", "p": ""}
    out = []
    for kind, text in to_blocks(bundle):
        out.append(("\n" if kind != "li" else "") + prefix[kind] + text)
    return ("\n".join(out).lstrip("\n") + "\n").encode("utf-8")


def to_json(bundle: dict) -> bytes:
    return json.dumps({**bundle, "disclaimer": DISCLAIMER}, indent=2, ensure_ascii=False).encode("utf-8")


def to_pdf(bundle: dict) -> bytes:
    # NOTE: reportlab's built-in Helvetica covers Latin scripts only. Register a TTF font to export
    # other scripts (see docs/security.md "Known limitations").
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    ss = getSampleStyleSheet()
    styles = {"h1": ss["Title"], "h2": ss["Heading2"], "h3": ss["Heading3"], "p": ss["BodyText"], "li": ss["BodyText"]}
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title=bundle["campaign"].get("name", "Campaign"))
    story = []
    for kind, text in to_blocks(bundle):
        if kind == "li":
            story.append(Paragraph(escape(text), styles["li"], bulletText="\u2022"))
        else:
            story.append(Paragraph(escape(text), styles[kind]))
        if kind == "h1":
            story.append(Spacer(1, 4))
    doc.build(story)
    return buf.getvalue()


RENDERERS = {
    "txt": (to_txt, "text/plain; charset=utf-8"),
    "md": (to_markdown, "text/markdown; charset=utf-8"),
    "json": (to_json, "application/json"),
    "pdf": (to_pdf, "application/pdf"),
}
