"""Code checks on the model's reading, and the merge with the rules.

A model claim is shown as verified only when its quote is on a page of the PDF and the quote supports it:
an entity type's quote names that type (or a class phrase that covers it); a date's quote contains the date,
or "with immediate effect"-style words and the date is the notification date, or "six months from the date of
this circular"-style words that compute to it. Anything else is shown as "check the document", never as fact.

Versions, all built from the same model answer so each layer's value is measured:
- rules:   the rules alone
- model:   the model's answer as given
- checked: the model's answer with the checks
- union:   rules + checked model (what ships): entity types from either; dates where they agree, or from
           whichever one is verified, withheld where they disagree
"""
import datetime as dt
import re

from . import entities
from .text import IMMEDIATE, dates_in, find_quote, relative_date

ISO = re.compile(r"^20\d\d-\d\d-\d\d$")
VERSIONS = ("rules", "model", "checked", "union")


def _iso(v) -> str | None:
    v = (v or "").strip()
    return v if ISO.match(v) else None


# A date's quote must say what the date is for, not just contain it (the letterhead date isn't a commencement).
PURPOSE = {
    "effective_date": re.compile(r"effect|force|effective|w\.\s?e\.\s?f|commenc|operational|applicable|withdrawn|"
                                 r"revised|implement", re.I),
    "comply_by": re.compile(r"\b(?:shall|should|must|required|advised|ensure|complete|submit|submitted|put in place|"
                            r"phased out|comply|migrat|report)", re.I),
    "comments_by": re.compile(r"comment|feedback|suggestion", re.I),
}


def date_supported(value: str, quote: str, on_page: int | None, issued: dt.date | None, field: str | None = None) -> bool:
    if on_page is None or not _iso(value):
        return False
    if field in PURPOSE and not PURPOSE[field].search(quote or ""):
        return False
    d = dt.date.fromisoformat(value)
    if d in dates_in(quote):
        return True
    if issued and relative_date(quote, issued) == d:
        return True
    return bool(issued and d == issued and IMMEDIATE.search(quote or ""))


def from_model(answer: dict, pages: list[str], issued: dt.date | None) -> dict:
    """The model's answer, normalised, with each claim's check result."""
    types: dict[str, dict] = {}
    for a in answer.get("applies_to") or []:
        t, quote = a.get("entity_type"), a.get("quote") or ""
        if t not in entities.TYPES:
            continue
        page = find_quote(quote, pages, a.get("page"))
        item = {"type": t, "page": page or a.get("page"), "quote": quote, "quote_ok": page is not None,
                "names_ok": entities.supports(quote, t)}
        item["verified"] = item["quote_ok"] and item["names_ok"]
        if t not in types or (item["verified"] and not types[t]["verified"]):
            types[t] = item

    def dated(obj, empty, field):
        obj = obj or {}
        raw = (obj.get("date") or "").strip()
        value = _iso(raw) or (empty if raw.lower() in ("", empty, "none", "not_stated", "not stated", "n/a") else None)
        quote = obj.get("quote") or ""
        page = find_quote(quote, pages, obj.get("page")) if quote else None
        verified = value == empty or date_supported(value or "", quote, page, issued, field)
        return {"value": value, "page": page or obj.get("page"), "quote": quote, "verified": bool(value and verified)}

    comply = []
    for c in answer.get("comply_by") or []:
        item = dated(c, "none", "comply_by")
        if item["value"] and item["value"] != "none":
            item["what"] = c.get("what") or ""
            comply.append(item)
    aq = answer.get("action_quote") or ""
    return {
        "applies_to": list(types.values()),
        "kind": answer.get("kind"),
        "action_required": answer.get("action_required"),
        "action": answer.get("action") or "",
        "action_evidence": {"page": find_quote(aq, pages, answer.get("action_page")), "quote": aq},
        "effective_date": dated(answer.get("effective_date"), "not_stated", "effective_date"),
        "comply_by": comply,
        "comments_by": dated(answer.get("comments_by"), "none", "comments_by"),
        "amends": answer.get("amends") or "none",
    }


def _merge_date(rule: dict | None, model: dict | None, empty: str) -> dict:
    """Rules' date (always quoted) against the model's checked date."""
    r = rule if rule and rule.get("value") not in (None, empty) else None
    m = model if model and model.get("verified") else None
    if r and m and m["value"] not in (empty, r["value"]):
        return {"value": None, "status": "check", "note": f"rules read {r['value']}, model read {m['value']}",
                "page": r["page"], "quote": r["quote"]}
    if r:
        return {"value": r["value"], "status": "verified", "page": r["page"], "quote": r["quote"],
                "source": "both" if m and m["value"] == r["value"] else "rules"}
    if m:
        return {"value": m["value"], "status": "verified" if m["value"] != empty else empty,
                "page": m.get("page"), "quote": m.get("quote"), "source": "model"}
    if model and model.get("value") and model["value"] != empty:
        return {"value": None, "status": "check", "note": f"model read {model['value']} but its quote doesn't show it",
                "page": model.get("page"), "quote": model.get("quote")}
    return {"value": empty, "status": empty, "page": None, "quote": None}


def card(version: str, rules: dict, model: dict | None) -> dict:
    """One notification's answer under a version: what's shown, with evidence and status."""
    if version == "rules" or model is None:
        r_eff, r_com = rules["effective_date"], rules["comments_by"]
        return {
            "applies_to": [dict(a, source="rules", status="verified") for a in rules["applies_to"]],
            "kind": (rules["kind"] or {}).get("value"),
            "action_required": (rules["action_required"] or {}).get("value"), "action": "", "action_evidence": None,
            "effective_date": dict(r_eff, status="verified" if r_eff["value"] != "not_stated" else "not_stated"),
            "comply_by": [dict(c, status="verified") for c in rules["comply_by"]],
            "comments_by": dict(r_com, status="verified" if r_com["value"] != "none" else "none"),
            "amends": None,
        }
    if version == "model":
        def raw(d, empty):
            return dict(d, status="verified" if d["value"] not in (None, empty) else (d["value"] or "check"))
        return {
            "applies_to": [dict(a, source="model", status="verified") for a in model["applies_to"]],
            "kind": model["kind"], "action_required": model["action_required"], "action": model["action"],
            "action_evidence": model["action_evidence"],
            "effective_date": raw(model["effective_date"], "not_stated"),
            "comply_by": [dict(c, status="verified") for c in model["comply_by"]],
            "comments_by": raw(model["comments_by"], "none"), "amends": model["amends"],
        }

    def checked(d, empty):
        if d["value"] == empty:
            return dict(d, status=empty)
        return dict(d, status="verified" if d["verified"] else "check")

    out = {
        "applies_to": [dict(a, source="model", status="verified") for a in model["applies_to"] if a["verified"]],
        "kind": model["kind"], "action_required": model["action_required"], "action": model["action"],
        "action_evidence": model["action_evidence"] if model["action_evidence"]["page"] else None,
        "effective_date": checked(model["effective_date"], "not_stated"),
        "comply_by": [dict(c, status="verified" if c["verified"] else "check") for c in model["comply_by"]],
        "comments_by": checked(model["comments_by"], "none"), "amends": model["amends"],
    }
    if version == "checked":
        return out
    # union
    by_type = {a["type"]: dict(a, source="rules", status="verified") for a in rules["applies_to"]}
    for a in out["applies_to"]:
        if a["type"] in by_type:
            by_type[a["type"]]["source"] = "both"
        else:
            by_type[a["type"]] = a
    rule_eff = rules["effective_date"] if rules["effective_date"]["value"] != "not_stated" else None
    rule_com = rules["comments_by"] if rules["comments_by"]["value"] != "none" else None
    # Deadlines: the model's checked ones are shown; one the rules found that the model didn't is "check".
    comply = {c["value"]: c for c in out["comply_by"]}
    for c in rules["comply_by"]:
        if c["value"] in comply:
            comply[c["value"]].update(status="verified", source="both")
        else:
            comply[c["value"]] = dict(c, status="check", source="rules",
                                      note="found by the rules only; read the clause before relying on it")
    out.update({
        "applies_to": list(by_type.values()),
        "kind": (rules["kind"] or {}).get("value") or model["kind"],
        "effective_date": _merge_date(rule_eff, model["effective_date"], "not_stated"),
        "comply_by": sorted(comply.values(), key=lambda c: c["value"]),
        "comments_by": _merge_date(rule_com, model["comments_by"], "none"),
    })
    return out


def prediction(c: dict) -> dict:
    """The card reduced to what's scored."""
    def shown(d, empty):
        if d["status"] == "check" or d.get("value") is None:
            return "withheld"
        return d["value"] if d["status"] == "verified" else empty
    comply = {x["value"] for x in c["comply_by"] if x["status"] == "verified"}
    return {
        "applies_to": {a["type"] for a in c["applies_to"]},
        "kind": c["kind"], "action_required": c["action_required"],
        "effective_date": shown(c["effective_date"], "not_stated"),
        "comply_by": comply, "comply_unverified": any(x["status"] == "check" for x in c["comply_by"]),
        "comments_by": shown(c["comments_by"], "none"),
    }
