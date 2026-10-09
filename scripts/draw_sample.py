"""Draw the evaluation set from the population of RBI notifications, before any labelling.

    python -m scripts.draw_sample

Reads data/population.jsonl (every notification from 1 April to 7 October 2026, ids 13360-13735),
tags each with a coarse kind from its title alone (for stratifying, not for scoring), and draws a
seeded random sample stratified by that tag: at least FLOOR per tag, the rest in proportion. Each tag's
draw is then split into development and held-out documents. Writes data/sample.json.

The random draw picked no notification on payment systems, which are what the fintech licences the
product is pitched at (payment aggregators, PPI issuers, payment system operators) live under. So every
other notification that regulates payments is added as a separate "payments" stratum, chosen by a rule
from the population list alone (is_payments, below) and split with its own seed. It isn't random, so
results are reported for the random draw and the supplement separately.
"""
import collections
import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = 20261009          # the day the population was frozen
TOTAL, FLOOR, DEV_SHARE = 50, 4, 0.4
SUPPLEMENT_SEED = SEED + 1


def is_payments(rec: dict) -> bool:
    """Issued by the Department of Payment and Settlement Systems, or titled about payments regulation."""
    t = (rec.get("title") or "").lower()
    return "dpss" in (rec.get("head") or "").lower() or any(w in t for w in ("digital payment", "payment system", "non-bank entit"))


def title_tag(rec: dict) -> str:
    t = (rec.get("title") or "").lower()
    head = (rec.get("head") or "").lower()
    if "draft" in t:
        return "draft"
    if "a.p. (dir series)" in head or "a. p. (dir series)" in head:
        return "fx"
    if "withdraw" in t or "repeal" in t:
        return "withdrawal"
    if "amendment" in t:
        return "amendment"
    if any(w in t for w in ("liquidity adjustment", "auction", "repo", "bank rate", "standing", "treasury bill",
                            "government securities", "sovereign gold", "primary dealer", "cash reserve", "ways and means")):
        return "rates_operational"
    if "directions" in t or "framework" in t:
        return "new_direction"
    return "other"


def main() -> int:
    pop = [json.loads(line) for line in (ROOT / "data" / "population.jsonl").read_text(encoding="utf-8").splitlines()]
    usable = [r for r in pop if r.get("pdf") and r.get("title") and not r.get("error")]
    by_tag = collections.defaultdict(list)
    for r in usable:
        by_tag[title_tag(r)].append(r)
    rng = random.Random(SEED)
    tags = sorted(by_tag)
    quota = {t: min(FLOOR, len(by_tag[t])) for t in tags}
    rest = TOTAL - sum(quota.values())
    pool = sum(len(by_tag[t]) - quota[t] for t in tags)
    for t in tags:   # proportional share of the remainder, rounded down, then topped up largest-first
        quota[t] += (len(by_tag[t]) - quota[t]) * rest // pool if pool else 0
    for t in sorted(tags, key=lambda t: -len(by_tag[t])):
        if sum(quota.values()) >= TOTAL:
            break
        if quota[t] < len(by_tag[t]):
            quota[t] += 1
    picked = []
    for t in tags:
        draw = rng.sample(sorted(by_tag[t], key=lambda r: r["id"]), quota[t])
        n_dev = round(len(draw) * DEV_SHARE)
        for i, r in enumerate(draw):
            picked.append({"id": r["id"], "tag": t, "split": "dev" if i < n_dev else "holdout", "title": r["title"],
                           "rbi_no": r.get("rbi_no"), "date": r.get("date"), "url": r["url"], "pdf": r["pdf"]})
    drawn = {r["id"] for r in picked}
    extra = sorted((r for r in usable if r["id"] not in drawn and is_payments(r)), key=lambda r: r["id"])
    random.Random(SUPPLEMENT_SEED).shuffle(extra)
    n_dev = round(len(extra) * DEV_SHARE)
    for i, r in enumerate(extra):
        picked.append({"id": r["id"], "tag": "payments", "split": "dev" if i < n_dev else "holdout", "title": r["title"],
                       "rbi_no": r.get("rbi_no"), "date": r.get("date"), "url": r["url"], "pdf": r["pdf"],
                       "supplement": True})
    picked.sort(key=lambda r: (r["split"], r["id"]))
    out = {"seed": SEED, "supplement_seed": SUPPLEMENT_SEED, "population": len(pop), "usable": len(usable),
           "per_tag": {t: {"population": len(by_tag[t]), "drawn": quota[t]} for t in tags},
           "supplement": {"rule": "not drawn, and issued by DPSS or titled 'digital payment', 'payment system' or 'non-bank entit(y|ies)'",
                          "added": len(extra)},
           "documents": picked}
    with open(ROOT / "data" / "sample.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    for t in tags:
        print(f"  {t:18} population {len(by_tag[t]):4}  drawn {quota[t]:3}")
    print(f"  {'payments (rule)':18} added {len(extra):3}: {', '.join(str(r['id']) for r in sorted(extra, key=lambda r: r['id']))}")
    print(f"{len(picked)} drawn from {len(usable)} usable of {len(pop)}: "
          f"{sum(r['split'] == 'dev' for r in picked)} dev, {sum(r['split'] == 'holdout' for r in picked)} held out")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
