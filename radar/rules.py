"""Rules: what can be read from a notification's structure without a model.

Since RBI's 2025 consolidation, directions name their entity type in the title ("Reserve Bank of India
(Payments Banks – ...) Directions"), circulars carry an addressee line ("All banks", "To All Authorised
Dealers"), and most directions have an applicability sentence and a commencement sentence. Each rule
returns the exact text it matched as its quote, so its claims pass the quote check by construction.
"""
import re

from . import entities
from .text import DATE_RE, IMMEDIATE, dates_in, find_quote, relative_date

TITLE = re.compile(r"Reserve Bank of India\s*[\(\[]\s*([^)\]]{3,200}?)\s*[\)\]]\s*(?:\(?[A-Za-z]+\)?\s+){0,3}?"
                   r"(?:Amendment\s+)?(?:Supervisory\s+)?Directions?(?:,\s*20\d\d)?", re.I)
APPLIES = re.compile(r"(?:These|The provisions (?:contained )?(?:in|of) these|The provisions of this)\s+(?:Amendment\s+)?"
                     r"(?:Master\s+)?(?:Supervisory\s+)?(?:Directions?|circular|framework|guidelines)\s+"
                     r"(?:shall|will|are|is)?\s*(?:be\s+)?(?:applicable|apply)\s+to\b[^.;]{0,300}", re.I)
SENTENCE_END = re.compile(r"\(hereinafter|\.\s+(?=[A-Z0-9(])|;|\s\d{1,2}\.\s")
ADDRESSEE_END = re.compile(r"Madam|Dear Sir|Dear Madam|\bSir\s*[,/]", re.I)
AP_DIR = re.compile(r"A\.\s?P\.\s?\(DIR Series\)\s*Circular\s*No\.?\s*\d+", re.I)
COMMENCE = [re.compile(r"(?:shall|will)\s+come\s+into\s+(?:force|effect)[^.;]{0,160}", re.I),
            re.compile(r"(?:shall|will)\s+be\s+effective[^.;]{0,140}", re.I),
            re.compile(r"\b(?:effective|in force)\s+(?:immediately|from)[^.;]{0,100}", re.I),
            re.compile(r"[^.;]{0,120}with immediate effect", re.I)]
COMMENTS = re.compile(r"comments?\b[^.]{0,220}?(?:by|on or before|latest by|not later than|till|until|before)\s+(?:the\s+)?"
                      + DATE_RE.pattern, re.I)
DEADLINE = re.compile(r"[^.;]{0,200}\b(?:on or before|not later than|no later than|latest by|by|before)\s+(?:the\s+)?"
                      + DATE_RE.pattern + r"[^.;]{0,60}", re.I)
OBLIGATION = re.compile(r"\b(?:shall|should|must|are required|is required|are advised|ensure|complete|submit|put in place|"
                        r"phased out|comply)\b", re.I)


def _sentence(s: str) -> str:
    m = SENTENCE_END.search(s, 20)
    return (s[:m.start()] if m else s).strip()


def _add(out: dict, types, page: int, quote: str, why: str):
    for t in types:
        out.setdefault(t, {"type": t, "page": page, "quote": quote.strip(), "why": why})


def applies_to(pages: list[str], issued=None) -> list[dict]:
    found: dict[str, dict] = {}
    head = " ".join(pages[:2])
    # 1. the title names the entity type
    for i, page in enumerate(pages[:3], 1):
        for m in TITLE.finditer(page):
            who = re.split(r"\s+[–—-]\s+|\s[–—]|[–—]\s", m.group(1))[0]
            _add(found, entities.named_in(who), i, m.group(0), "title")
        if found:
            break
    # 2. the addressee line, between the date and "Madam / Sir"
    m = re.search(r"RBI/(?:[A-Za-z]+/)?20\d\d-\d\d/\d+", pages[0][:3000]) if pages else None
    if m:
        rest = pages[0][m.end(): m.end() + 700]
        d = DATE_RE.search(rest)
        if d:
            seg = rest[d.end():]
            end = ADDRESSEE_END.search(seg)
            if end and end.start() < 450:
                seg = seg[:end.start()].strip(" ,")
                _add(found, entities.named_in(seg), 1, seg[-300:], "addressee")
    # 3. the applicability sentence
    for i, page in enumerate(pages[:6], 1):
        for m in APPLIES.finditer(page):
            s = _sentence(m.group(0))
            _add(found, entities.named_in(s), i, s, "applicability")
    # 4. A.P. (DIR Series) circulars go to authorised dealers
    m = AP_DIR.search(head[:4000])
    if m:
        _add(found, ["authorised_dealers"], 1 if m.start() < len(pages[0]) else 2, m.group(0), "A.P. (DIR Series)")
    return list(found.values())


def kind(title: str) -> str | None:
    t = (title or "").lower()
    if re.search(r"\bdraft\b", t):
        return "draft"
    if re.search(r"withdrawal of (?:circulars|instructions|guidelines)|\brepeal", t):
        return "withdrawal"
    if re.search(r"consolidat", t) and "direction" not in t:
        return "other"
    if re.search(r"sanctions list|\bunsc\b|\buapa\b", t):
        return "other"
    if re.search(r"\bfaqs?\b|frequently asked|clarification|corrigendum", t):
        return "clarification"
    if re.search(r"\bamendment", t):
        return "amendment"
    if re.search(r"bank rate|\brepo\b|liquidity adjustment|\blaf\b|auction|treasury bill|ways and means|penal interest|"
                 r"standing (?:deposit|liquidity)|marginal standing|facility\b|\breturns?\b|reporting|submission|portal", t):
        return "rates_operational"
    if re.search(r"directions?|framework|guidelines|scheme", t):
        return "new_direction"
    return None


def effective_date(pages: list[str], issued) -> dict | None:
    for pat in COMMENCE:
        for i, page in enumerate(pages[:8], 1):
            for m in pat.finditer(page):
                s = m.group(0).strip()
                ds = dates_in(s)
                rel = relative_date(s, issued) if issued else None
                if ds:
                    value = ds[0]
                elif rel:
                    value = rel
                elif issued and IMMEDIATE.search(s):
                    value = issued
                else:
                    continue
                return {"value": value.isoformat(), "page": i, "quote": s}
    return None


def comments_by(pages: list[str]) -> dict | None:
    for i, page in enumerate(pages, 1):
        m = COMMENTS.search(page)
        if m:
            ds = dates_in(m.group(0))
            if ds:
                return {"value": ds[-1].isoformat(), "page": i, "quote": m.group(0).strip()}
    return None


def comply_by(pages: list[str], exclude=()) -> list[dict]:
    out, seen = [], set(exclude)
    for i, page in enumerate(pages, 1):
        for m in DEADLINE.finditer(page):
            s = m.group(0).strip()
            if not OBLIGATION.search(s) or re.search(r"come into|w\.e\.f|with effect from|dated|substituted|"
                                                     r"inserted|vide|issued on|updated (?:as on|upto)", s, re.I):
                continue
            for d in dates_in(s):
                iso = d.isoformat()
                if iso not in seen:
                    seen.add(iso)
                    out.append({"value": iso, "what": "", "page": i, "quote": s})
    return out


def read(pages: list[str], title: str, issued) -> dict:
    """Everything the rules can say about one notification, in the same shape as a checked model reading."""
    k = kind(title)
    eff = effective_date(pages, issued)
    q = find_quote(title, pages)
    return {
        "applies_to": applies_to(pages, issued),
        "kind": {"value": k, "page": q, "quote": title if q else None} if k else None,
        "action_required": {"value": "no" if k in ("draft", "withdrawal", "clarification") else "yes",
                            "page": None, "quote": None, "action": ""} if k else None,
        "effective_date": eff or {"value": "not_stated", "page": None, "quote": None},
        "comply_by": comply_by(pages, exclude=[eff["value"]] if eff else []),
        "comments_by": comments_by(pages) or {"value": "none", "page": None, "quote": None},
        "amends": None,
    }
