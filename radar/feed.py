"""RBI's notifications, by id: title, date, RBI number and PDF link from the notification's page.

RBI numbers its notifications sequentially (https://www.rbi.org.in/scripts/NotificationUser.aspx?Id=13736),
so new ones are found by probing forward from the last id seen until several ids in a row are empty.
Requests are spaced out to be polite to RBI's servers.
"""
import html
import re
import time

import httpx

from .text import parse_date

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/130.0 Safari/537.36 rbi-circular-radar/1.0"}
PAGE = "https://www.rbi.org.in/scripts/NotificationUser.aspx?Id={id}&Mode=0"
PAUSE = 1.5


def meta(nid: int, client: httpx.Client | None = None) -> dict | None:
    """One notification's metadata, or None if the id has no notification (yet)."""
    c = client or httpx.Client(headers=UA, timeout=60, follow_redirects=True)
    s = c.get(PAGE.format(id=nid)).text
    title = re.search(r"alt='PDF - ([^']+)'", s)
    pdf = re.findall(r'href="(https://rbidocs\.rbi\.org\.in/rdocs/notification/PDFs/[^"]+)"', s, re.I)
    if not title or not pdf:
        return None
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))
    num = re.search(r"RBI/(?:[A-Za-z]+/)?20\d\d-\d\d/\d+", txt)
    head = txt[num.start(): num.start() + 500] if num else ""
    d = re.search(r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
                  r"\s+\d{1,2},\s+20\d\d", head)
    issued = parse_date(d.group(0)) if d else None
    return {"id": nid, "url": PAGE.format(id=nid), "rbi_no": num.group(0) if num else None,
            "date": issued.isoformat() if issued else None,
            "title": re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", title.group(1)))).strip(),
            "pdf": pdf[0]}


def new_since(last_id: int, max_misses: int = 5, limit: int = 60) -> list[dict]:
    """Notifications after last_id, stopping after max_misses empty ids in a row."""
    out, misses, nid = [], 0, last_id
    with httpx.Client(headers=UA, timeout=60, follow_redirects=True) as c:
        while misses < max_misses and len(out) < limit:
            nid += 1
            m = meta(nid, c)
            time.sleep(PAUSE)
            if m:
                out.append(m)
                misses = 0
            else:
                misses += 1
    return out


def pdf_bytes(url: str) -> bytes:
    r = httpx.get(url, headers=UA, timeout=120, follow_redirects=True)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise ValueError(f"{url} did not return a PDF")
    return r.content
