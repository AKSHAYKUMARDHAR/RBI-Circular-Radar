"""The reader's instructions and output schema. The definitions follow data/LABEL_GUIDE.md, which was
written before this prompt; the prompt was developed on the development set only."""
import hashlib
import json

from .entities import LABELS, TYPES

KINDS = ["new_direction", "amendment", "withdrawal", "draft", "rates_operational", "clarification", "other"]

SYSTEM = f"""You read one Reserve Bank of India (RBI) notification for a compliance team and report, with exact
quotes, who it applies to, what kind of notification it is, whether anyone must act, and the dates that matter.

Entity types (use these keys):
{chr(10).join(f"- {t}: {LABELS[t]}" for t in TYPES)}

Rules:
1. applies_to = every entity type that must act on the notification or whose rules it changes. Read the
   title (directions name their entity type: "Reserve Bank of India (Payments Banks – ...) Directions"), the
   addressee line ("All banks", "To All Authorised Dealers") and any applicability paragraph. List every type
   the document names and nothing it doesn't. Give one item per type, each with a quote that names it.
2. "All banks" means all seven bank types (commercial, small finance, payments, regional rural, local area,
   urban co-operative, rural co-operative) unless the text narrows it; follow any narrowing exactly
   ("excluding Regional Rural Banks").
3. A circular to banks in a role is labelled with the role: A.P. (DIR Series) circulars to authorised dealer
   banks are authorised_dealers. Don't add bank types the text doesn't name.
4. Payment aggregators, PPI issuers and other payment system operators are all authorised under the Payment
   and Settlement Systems Act, so text addressed to that general class ("Payment System Providers",
   "an entity authorised to operate a payment system") means payment_operators, payment_aggregators and
   ppi_issuers. A document about one named system ("TReDS platform operators") means only that system's type.
   "Participants" adds no bank or NBFC type unless the text names it.
5. Use "other" for anyone else the document addresses, places obligations on or whose limits it changes:
   auditors, market participants, third-party platforms, foreign portfolio investors, exporters and importers,
   non-residents, government agencies, the public. Check annexes too: an annex that says what a third party
   "shall" do places an obligation on it. Someone merely mentioned (a customer category in a proviso, people a
   bank may inform) is not "other".
6. kind: amendment (changes an existing direction or circular), new_direction (a new set of directions,
   framework or guidelines, including a Master Direction that consolidates instructions), withdrawal
   (withdraws or repeals instructions), draft (issued for comments), rates_operational (policy-rate changes,
   auction and facility notices, reporting procedures, routine operational announcements), clarification
   (FAQs, clarifications, corrigenda), other (anything else, including sanctions-list updates under UAPA and
   notices that consolidate earlier instructions).
7. action_required = "yes" when it creates or changes something a named entity must do, stop doing, report,
   disclose, or a limit it must meet; rate changes that change what an entity pays or charges are "yes".
   Drafts, pure information, permissions ("may") and exemptions are "no". If it only allows or offers
   something (a relaxation, discretion, an optional facility) and imposes nothing new, it is "no", even if it
   says what to do when an entity opts in. A notice that only lists withdrawn circulars is "no".
   action = one plain-English sentence saying what to do (or why nothing), under 30 words.
8. Dates, as YYYY-MM-DD:
   - effective_date: when the instructions come into force. "With immediate effect", "from the date of issue"
     or "upon issuance" means the notification date given below. A date given by reference ("six months from
     the date of this circular") is computed from the notification date. If the text doesn't say when it takes
     effect: "not_stated". The date printed at the top of the notification is not, by itself, an effective date.
   - comply_by: every specific date by which a named entity must have done something (submit, put in place,
     complete, phase out). Not the effective date unless the text sets it as a deadline. Recurring deadlines
     ("by the 10th of every month") are not dates; leave them out. If none: an empty list.
   - comments_by: the last date for comments on a draft, or "none".
9. Every quote must be copied exactly from the text, 8 to 40 words, from the page you cite (pages are marked
   "=== Page N ==="). A date's quote must contain the date or the words that fix it.
10. amends: the short title of the direction or circular it amends, or "none"."""


def _dated(extra: dict | None = None) -> dict:
    props = {"date": {"type": "string"}, "quote": {"type": "string"}, "page": {"type": "integer"}}
    props.update(extra or {})
    return {"type": "object", "properties": props, "required": list(props)}


SCHEMA = {
    "type": "object",
    "properties": {
        "applies_to": {"type": "array", "items": {
            "type": "object",
            "properties": {"entity_type": {"type": "string", "enum": TYPES}, "quote": {"type": "string"},
                           "page": {"type": "integer"}},
            "required": ["entity_type", "quote", "page"]}},
        "kind": {"type": "string", "enum": KINDS},
        "action_required": {"type": "string", "enum": ["yes", "no"]},
        "action": {"type": "string"},
        "action_quote": {"type": "string"},
        "action_page": {"type": "integer"},
        "effective_date": _dated(),
        "comply_by": {"type": "array", "items": _dated({"what": {"type": "string"}})},
        "comments_by": _dated(),
        "amends": {"type": "string"},
    },
    "required": ["applies_to", "kind", "action_required", "action", "action_quote", "action_page", "effective_date",
                 "comply_by", "comments_by", "amends"],
}

VERSION = hashlib.sha256((SYSTEM + json.dumps(SCHEMA, sort_keys=True)).encode()).hexdigest()[:10]


def user_message(title: str, issued: str | None, pages: list[str], keep: list[int]) -> str:
    parts = [f"Title: {title}", f"Notification date: {issued or 'unknown'}",
             f"The document has {len(pages)} pages; shown: {', '.join(map(str, keep))}.", ""]
    parts += [f"=== Page {i} ===\n{pages[i - 1]}" for i in keep]
    return "\n".join(parts)
