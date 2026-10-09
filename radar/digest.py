"""Build the digest the site shows: every RBI notification read, checked and merged.

    python -m radar.digest --new                 # every 10 minutes: notifications after the last one read
    python -m radar.digest --ids 13690-13736     # backfill a range
    python -m radar.digest --retry               # re-read notifications whose model read failed earlier

Each notification goes through the shipped pipeline (radar/checks.py): rules + one gemini-3.5-flash-lite read,
code checks on every quote and date, entity types the check can't confirm shown as "may apply: check".
If the model can't be reached (daily quota), the rules' reading is published, marked "rules only", and retried
on the next run. Model answers are cached in data/answers/ by document hash.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import time

import httpx

from . import checks, entities, feed, prompts, rules
from .text import issue_date, pages_of

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "notifications.json"
ANSWERS = ROOT / "data" / "answers"


def _evidence(d: dict | None) -> dict | None:
    if not d:
        return None
    keep = {k: d.get(k) for k in ("value", "status", "page", "quote", "note", "what", "source") if d.get(k) not in (None, "")}
    return keep


def build_record(m: dict, reader) -> dict:
    pdf = feed.pdf_bytes(m["pdf"])
    sha = hashlib.sha256(pdf).hexdigest()
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "n.pdf"
        path.write_bytes(pdf)
        pages = pages_of(path)
    issued = issue_date(pages, m.get("date"))
    rr = rules.read(pages, m["title"], issued)
    model, error = None, None
    if reader:
        try:
            out = reader.read(f"R{m['id']}", sha, m["title"], issued.isoformat() if issued else None, pages)
            model = checks.from_model(out["answer"], pages, issued)
        except Exception as e:   # quota or transport: publish the rules' reading, retry next run
            error = f"{type(e).__name__}: {str(e)[:160]}"
    c = checks.card("shipped" if model else "rules", rr, model)
    return {
        "id": m["id"], "rbi_no": m.get("rbi_no"), "date": issued.isoformat() if issued else m.get("date"),
        "title": m["title"], "url": m["url"], "pdf": m["pdf"], "pages": len(pages), "sha256": sha,
        "kind": c["kind"], "action_required": c["action_required"], "action": c.get("action") or "",
        "action_evidence": c.get("action_evidence"),
        "applies_to": [dict(_evidence(a), type=a["type"], label=entities.LABELS[a["type"]]) for a in c["applies_to"]],
        "effective_date": _evidence(c["effective_date"]),
        "comply_by": [_evidence(x) for x in c["comply_by"]],
        "comments_by": _evidence(c["comments_by"]),
        "amends": c.get("amends") if c.get("amends") not in (None, "none") else None,
        "reader": {"model": reader.model if model else None, "prompt_version": prompts.VERSION if model else None,
                   "rules_only": model is None, "error": error},
        "read_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def load() -> dict:
    if OUT.exists():
        return json.loads(OUT.read_text(encoding="utf-8"))
    return {"notifications": []}


def save(data: dict) -> None:
    data["notifications"].sort(key=lambda r: r["id"], reverse=True)
    data["generated_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["entity_types"] = [{"type": t, "label": entities.LABELS[t]} for t in entities.TYPES]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new", action="store_true")
    g.add_argument("--ids", help="a range like 13690-13736, or a comma list")
    g.add_argument("--retry", action="store_true")
    ap.add_argument("--no-model", action="store_true")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    reader = None
    if not args.no_model:
        from .llm import GeminiReader
        reader = GeminiReader(cache_dir=ANSWERS)
    data = load()
    have = {r["id"]: r for r in data["notifications"]}
    if args.new:
        last = max(have) if have else 13735
        todo = feed.new_since(last)
    elif args.retry:
        todo = [{k: r[k] for k in ("id", "url", "rbi_no", "date", "title", "pdf")}
                for r in have.values() if r["reader"]["rules_only"]]
    else:
        if "-" in args.ids:
            a, b = map(int, args.ids.split("-"))
            ids = range(a, b + 1)
        else:
            ids = [int(x) for x in args.ids.split(",")]
        todo = []
        with httpx.Client(headers=feed.UA, timeout=60, follow_redirects=True) as c:
            for nid in ids:
                if nid in have and not have[nid]["reader"]["rules_only"]:
                    continue
                m = feed.meta(nid, c)
                if m:
                    todo.append(m)
                time.sleep(feed.PAUSE)
    print(f"{len(todo)} notifications to read")
    changed = 0
    for m in todo:
        try:
            rec = build_record(m, reader)
        except Exception as e:
            print(f"  {m['id']}: skipped ({type(e).__name__}: {str(e)[:120]})")
            continue
        old = have.get(m["id"])
        if old and rec["reader"]["rules_only"] and old["reader"]["rules_only"]:
            print(f"  {m['id']}: model still unavailable, kept as rules only")
            continue   # a failed retry changes nothing, so it isn't published again
        have[m["id"]] = rec
        changed += 1
        flag = " (rules only)" if rec["reader"]["rules_only"] else ""
        print(f"  {m['id']} {rec['date']} {', '.join(a['type'] for a in rec['applies_to'])}{flag}")
        data["notifications"] = list(have.values())
        save(data)   # after each one, so a stopped run keeps what it read
    # Runs with nothing new write nothing, so frequent checks don't commit or republish the site.
    if changed and os.getenv("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write("changed=true\n")
    print(f"{changed} published")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
