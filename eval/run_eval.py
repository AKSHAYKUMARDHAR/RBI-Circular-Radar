"""Score the radar against the hand-written answer keys.

    python -m eval.run_eval --split dev                          # rules + gemini-3.5-flash-lite, one read
    python -m eval.run_eval --split dev --model gemini-3.5-flash --reads 2
    python -m eval.run_eval --split dev --no-model               # rules only, no requests
    python -m eval.run_eval --split holdout                      # release run 1: once
    python -m eval.run_eval --split holdout2                     # release run 2, on a fresh draw: once

Every version (rules, model, checked, union) is scored from the same cached model answers
(eval/answers/), so comparing them costs nothing. Applicability is scored per (notification, entity type)
pair; a miss is the costly error. Dates are correct, wrong (a date shown that isn't the labelled one, or
"none" shown where there is one) or withheld (shown as "check the document"). The random draw and the
payments supplement are reported separately as well as together.
"""
import argparse
import collections
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from radar import checks, rules  # noqa: E402
from radar.text import issue_date, pages_of  # noqa: E402

GATE = {"missed": 0, "precision": 0.85, "wrong_dates": 0.02, "correct_dates": 0.85}
DATE_FIELDS = ("effective_date", "comply_by", "comments_by")


def merge_reads(reads: list[dict]) -> dict:
    """Two model reads: entity types from either (recall), dates kept only where both reads agree."""
    if len(reads) == 1:
        return reads[0]
    a, b = reads[0], reads[1]
    out = json.loads(json.dumps(a))
    have = {x["type"]: x for x in out["applies_to"]}
    for x in b["applies_to"]:
        if x["type"] not in have or (x["verified"] and not have[x["type"]]["verified"]):
            have[x["type"]] = x
    out["applies_to"] = list(have.values())
    for f in ("effective_date", "comments_by"):
        if a[f]["value"] != b[f]["value"]:
            out[f]["verified"] = False
    bd = {c["value"] for c in b["comply_by"]}
    for c in out["comply_by"]:
        c["verified"] = c["verified"] and c["value"] in bd
    if a["action_required"] != b["action_required"]:
        out["action_required"] = "yes"   # recall-first: flag for review rather than miss an obligation
    return out


def score_dates(label: dict, pred: dict) -> dict:
    res = {}
    for f in DATE_FIELDS:
        lv = label[f]["value"]
        if lv == "skip":
            continue
        p = pred[f]
        if f == "comply_by":
            want, got, unsure = set(lv), p, pred["comply_unverified"]
            if got - want:
                res[f] = "wrong"
            elif got == want:
                res[f] = "correct"
            else:
                res[f] = "withheld" if unsure else "wrong"
        else:
            res[f] = "withheld" if p == "withheld" else ("correct" if p == lv else "wrong")
    return res


def summarise(rows: list[dict]) -> dict:
    tp = sum(r["tp"] for r in rows)
    fn = sum(len(r["missed"]) for r in rows)
    fp = sum(len(r["extra"]) for r in rows)
    dates = collections.Counter(v for r in rows for v in r["dates"].values())
    nd = sum(dates.values()) or 1
    kind = [r["kind_ok"] for r in rows if r["kind_ok"] is not None]
    act = [r["action_ok"] for r in rows if r["action_ok"] is not None]
    s = {"documents": len(rows), "pairs": tp + fn, "missed": fn, "extra": fp,
         "recall": tp / (tp + fn) if tp + fn else 1.0, "precision": tp / (tp + fp) if tp + fp else 1.0,
         "dates": dict(dates), "correct_dates": dates["correct"] / nd, "wrong_dates": dates["wrong"] / nd,
         "kind_accuracy": sum(kind) / len(kind) if kind else None,
         "action_accuracy": sum(act) / len(act) if act else None}
    s["gate"] = (s["missed"] <= GATE["missed"] and s["precision"] >= GATE["precision"]
                 and s["wrong_dates"] <= GATE["wrong_dates"] and s["correct_dates"] >= GATE["correct_dates"])
    return s


def fmt(name: str, s: dict) -> str:
    d = s["dates"]
    k = f"{s['kind_accuracy']:.0%}" if s["kind_accuracy"] is not None else "-"
    a = f"{s['action_accuracy']:.0%}" if s["action_accuracy"] is not None else "-"
    return (f"  {name:9} pairs {s['pairs']:3}  missed {s['missed']:2}  extra {s['extra']:2}  recall {s['recall']:6.1%}  "
            f"precision {s['precision']:6.1%} | dates {d.get('correct', 0):3} correct {d.get('wrong', 0):2} wrong "
            f"{d.get('withheld', 0):2} withheld ({s['correct_dates']:.0%} / {s['wrong_dates']:.1%}) | kind {k}  action {a}"
            f"  {'PASS' if s['gate'] else 'fail'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout", "holdout2"], required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--reads", type=int, default=1, choices=[1, 2])
    ap.add_argument("--no-model", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--show", action="store_true", help="print every document's differences")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")

    manifest = {d["id"]: d for d in json.loads((ROOT / "data" / "documents.json").read_text(encoding="utf-8"))["documents"]}
    labels = json.loads((ROOT / "data" / f"labels_{args.split}.json").read_text(encoding="utf-8"))["documents"]
    if args.only:
        keep = set(args.only.split(","))
        labels = [d for d in labels if d["id"] in keep]

    reader = None
    if not args.no_model:
        from radar.llm import GeminiReader, LLMError, QuotaExhausted
        reader = GeminiReader(model=args.model, cache_dir=ROOT / "eval" / "answers")
    versions = checks.VERSIONS if reader else ("rules",)
    rows = {v: [] for v in versions}
    usage = collections.Counter()
    unread, stopped = [], None
    t0 = time.time()
    for doc in labels:
        meta, L = manifest[doc["id"]], doc["labels"]
        pages = pages_of(ROOT / "data" / "pdfs" / f"{doc['id']}.pdf")
        issued = issue_date(pages, meta.get("date"))
        rr = rules.read(pages, meta["title"], issued)
        model = None
        if reader and not stopped:
            reads = []
            for attempt in range(args.reads):
                try:
                    out = reader.read(doc["id"], meta["sha256"], meta["title"], issued.isoformat() if issued else None,
                                      pages, attempt)
                    usage.update(out.get("usage") or {})
                    reads.append(checks.from_model(out["answer"], pages, issued))
                except QuotaExhausted as e:
                    stopped = str(e)
                    break
                except LLMError as e:
                    print(f"  {doc['id']}: model read failed: {e}")
            if len(reads) == args.reads:
                model = merge_reads(reads)
        if reader and model is None:
            unread.append(doc["id"])
            continue   # a document without a model reading isn't scored in any version, so versions stay comparable
        for v in versions:
            c = checks.card(v, rr, model)
            p = checks.prediction(c)
            gold = set(L["applies_to"]["value"]) if L["applies_to"]["value"] != "skip" else None
            row = {"id": doc["id"], "supplement": bool(meta.get("supplement")),
                   "tp": len(p["applies_to"] & gold) if gold is not None else 0,
                   "missed": sorted(gold - p["applies_to"]) if gold is not None else [],
                   "extra": sorted(p["applies_to"] - gold) if gold is not None else [],
                   "kind_ok": None if L["kind"]["value"] == "skip" else p["kind"] == L["kind"]["value"],
                   "action_ok": None if L["action_required"]["value"] == "skip" else p["action_required"] == L["action_required"]["value"],
                   "kind": p["kind"], "action": p["action_required"],
                   "pred_dates": {f: (sorted(p[f]) if f == "comply_by" else p[f]) for f in DATE_FIELDS},
                   "dates": score_dates(L, p)}
            rows[v].append(row)

    model_name = reader.model if reader else "none"
    print(f"\n{args.split}: {len(labels)} documents, model {model_name}, reads {args.reads if reader else 0}"
          f"{f', {len(unread)} without a model reading (not scored): ' + ', '.join(unread) if unread else ''}")
    if stopped:
        print(f"  stopped calling the model: {stopped}")
    summary = {}
    for group, pick in (("all", lambda r: True), ("random draw", lambda r: not r["supplement"]),
                        ("supplement", lambda r: r["supplement"])):
        print(f"\n {group}")
        summary[group] = {}
        for v in versions:
            sel = [r for r in rows[v] if pick(r)]
            if not sel:
                continue
            s = summarise(sel)
            summary[group][v] = s
            print(fmt(v, s))
    for v in versions:
        bad = [r for r in rows[v] if r["missed"] or (args.show and (r["extra"] or "wrong" in r["dates"].values()))]
        if bad:
            print(f"\n {v}: problems")
            for r in rows[v]:
                lab = next(d["labels"] for d in labels if d["id"] == r["id"])
                wrong = {f: (r["pred_dates"][f], lab[f]["value"]) for f, s in r["dates"].items() if s != "correct"}
                if r["missed"] or (args.show and (r["extra"] or wrong or not r["kind_ok"] or not r["action_ok"])):
                    print(f"  {r['id']}: missed {r['missed']} extra {r['extra']}"
                          f"{'' if r['kind_ok'] else ' kind ' + str(r['kind']) + '/' + lab['kind']['value']}"
                          f"{'' if r['action_ok'] else ' action ' + str(r['action']) + '/' + lab['action_required']['value']}"
                          f" dates {wrong if wrong else 'ok'}")
    print(f"\n tokens: {dict(usage)}   {time.time() - t0:.0f}s")
    out = ROOT / "eval" / "results" / f"{args.split}_{model_name}_r{args.reads if reader else 0}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"split": args.split, "model": model_name, "reads": args.reads, "unread": unread,
                               "stopped": stopped, "summary": summary, "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
