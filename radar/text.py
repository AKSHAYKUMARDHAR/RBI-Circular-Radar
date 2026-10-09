"""PDF text, quote matching and dates.

Quotes are matched on letters and digits only (after Unicode NFKC), the same comparison the answer-key
checker uses, because text extracted from PDFs loses or adds spaces and hyphens.
"""
import datetime as dt
import re
import unicodedata

from pypdf import PdfReader

MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
_MON = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?"
DATE_RE = re.compile(rf"\b(?:{_MON}\s+\d{{1,2}}(?:st|nd|rd|th)?\s*,?\s+20\d\d|\d{{1,2}}(?:st|nd|rd|th)?\s+(?:of\s+)?{_MON}\s*,?\s+20\d\d|"
                     r"\d{1,2}[./-]\d{1,2}[./-]20\d\d)\b", re.I)


def pages_of(path) -> list[str]:
    """One string per PDF page, whitespace collapsed."""
    return [re.sub(r"\s+", " ", p.extract_text() or "").strip() for p in PdfReader(str(path)).pages]


def compact(s: str) -> str:
    return re.sub(r"[^0-9a-z]", "", unicodedata.normalize("NFKC", s or "").lower())


def find_quote(quote: str, pages: list[str], page: int | None = None) -> int | None:
    """The 1-based page the quote is on (the stated page first), or None. Quotes under 12 letters don't count."""
    q = compact(quote)
    if len(q) < 12:
        return None
    order = ([page] if page and 1 <= page <= len(pages) else []) + [i for i in range(1, len(pages) + 1) if i != page]
    for i in order:
        if q in compact(pages[i - 1]):
            return i
    return None


def parse_date(s: str) -> dt.date | None:
    s = s.strip().rstrip(".")
    m = re.match(rf"({_MON})\s+(\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s+(20\d\d)$", s, re.I)
    if m:
        mon, day, year = m.group(1), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(rf"(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({_MON})\s*,?\s+(20\d\d)$", s, re.I)
        if m:
            day, mon, year = int(m.group(1)), m.group(2), int(m.group(3))
        else:
            m = re.match(r"(\d{1,2})[./-](\d{1,2})[./-](20\d\d)$", s)   # Indian order: day first
            if not m:
                return None
            try:
                return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                return None
    mon = mon.lower().rstrip(".")
    month = next((v for k, v in MONTHS.items() if k.startswith(mon[:3])), None)
    try:
        return dt.date(year, month, day) if month else None
    except ValueError:
        return None


def dates_in(text: str) -> list[dt.date]:
    return [d for d in (parse_date(m.group(0)) for m in DATE_RE.finditer(text or "")) if d]


def add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return dt.date(y, m, day)
        except ValueError:
            continue
    raise ValueError(d)


NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
           "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "thirty": 30, "sixty": 60, "ninety": 90}
RELATIVE = re.compile(r"\b(\d{1,3}|" + "|".join(NUMBERS) + r")\s+(months?|days?)\s+from the date of (?:(?:this|the|its)\s+)?"
                      r"(?:circular|notification|direction|directions|issue|issuance)", re.I)
IMMEDIATE = re.compile(r"immediate(?:ly)?\b|with immediate effect|from the date of (?:its )?(?:issue|issuance)|"
                       r"upon (?:its )?issuance|on the date of (?:its )?(?:issue|issuance)|date of issuance of this|"
                       r"placed on the website|from the date of this circular", re.I)


def relative_date(text: str, issued: dt.date) -> dt.date | None:
    """'six months from the date of this circular' -> the computed date."""
    m = RELATIVE.search(text or "")
    if not m:
        return None
    n = int(m.group(1)) if m.group(1).isdigit() else NUMBERS[m.group(1).lower()]
    return add_months(issued, n) if m.group(2).lower().startswith("month") else issued + dt.timedelta(days=n)


def issue_date(pages: list[str], fallback: str | None = None) -> dt.date | None:
    """The notification's date: the first date after the RBI reference number on page 1, else the listing date."""
    head = pages[0][:3000] if pages else ""
    m = re.search(r"RBI/(?:[A-Za-z]+/)?20\d\d-\d\d/\d+", head)
    if m:
        ds = dates_in(head[m.end(): m.end() + 400])
        if ds:
            return ds[0]
    if fallback:
        d = parse_date(fallback)
        if d:
            return d
    ds = dates_in(head)
    return ds[0] if ds else None
