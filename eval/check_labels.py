"""Check an answer key against the RBI PDFs: every quoted piece of evidence must appear on its cited page,
and every value must use the label guide's vocabulary.

    python -m eval.check_labels data/labels_dev.json

Quotes are compared on letters and digits only (after Unicode NFKC), because text extracted from PDFs
often loses or adds spaces and turns "fi" into a ligature.
"""
import json
import pathlib
import re
import sys
import unicodedata

from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENTITY_TYPES = {"commercial_banks", "small_finance_banks", "payments_banks", "regional_rural_banks", "local_area_banks",
                "urban_coop_banks", "rural_coop_banks", "aifis", "nbfcs", "arcs", "cics", "payment_aggregators",
                "ppi_issuers", "payment_operators", "authorised_dealers", "primary_dealers", "other"}
KINDS = {"new_direction", "amendment", "withdrawal", "draft", "rates_operational", "clarification", "other"}
FIELDS = ["applies_to", "kind", "action_required", "effective_date", "comply_by", "comments_by", "amends"]
DATE = re.compile(r"^20\d\d-\d\d-\d\d$")


def compact(s: str) -> str:
    return re.sub(r"[^0-9a-z]", "", unicodedata.normalize("NFKC", s or "").lower())


def valid(field: str, value) -> bool:
    if value == "skip":
        return True
    if field == "applies_to":
        return isinstance(value, list) and bool(value) and set(value) <= ENTITY_TYPES
    if field == "kind":
        return value in KINDS
    if field == "action_required":
        return value in ("yes", "no")
    if field == "effective_date":
        return value == "not_stated" or bool(DATE.match(str(value)))
    if field == "comply_by":
        return isinstance(value, list) and all(DATE.match(v) for v in value)
    if field == "comments_by":
        return value == "none" or bool(DATE.match(str(value)))
    return isinstance(value, str)   # amends


def check(path: str) -> int:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    bad = quoted = 0
    for doc in data["documents"]:
        reader = PdfReader(str(ROOT / "data" / "pdfs" / f"{doc['id']}.pdf"))
        pages = {i: compact(p.extract_text() or "") for i, p in enumerate(reader.pages, 1)}
        labels = doc["labels"]
        for field in FIELDS:
            if field not in labels:
                print(f"  {doc['id']}: missing {field}")
                bad += 1
                continue
            lab = labels[field]
            if not valid(field, lab["value"]):
                print(f"  {doc['id']}.{field}: value {lab['value']!r} is not in the label guide's vocabulary")
                bad += 1
            needs_quote = lab["value"] not in ("skip", "not_stated", "none", []) and field != "amends"
            if needs_quote and not lab.get("evidence"):
                print(f"  {doc['id']}.{field}: a value needs at least one quote")
                bad += 1
            for ev in lab.get("evidence", []):
                quoted += 1
                q, p = compact(ev["quote"]), ev["page"]
                if len(q) < 12 or p not in pages or q not in pages[p]:
                    where = [n for n, t in pages.items() if len(q) >= 12 and q in t]
                    print(f"  {doc['id']}.{field}: quote not on page {p} (found on {where}): {ev['quote'][:70]!r}")
                    bad += 1
        print(f"  {doc['id']}: ok" if not bad else f"  {doc['id']}: checked")
    print(f"{len(data['documents'])} documents, {quoted} quotes, {bad} problems")
    return bad


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(1 if check(sys.argv[1]) else 0)
