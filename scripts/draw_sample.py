"""Draw the evaluation set from the population of RBI notifications, before any labelling.

    python -m scripts.draw_sample

Reads data/population.jsonl (every notification from 1 April to 7 October 2026, ids 13360-13735),
tags each with a coarse kind from its title alone (for stratifying, not for scoring), and draws a
seeded random sample stratified by that tag: at least FLOOR per tag, the rest in proportion. Each tag's
draw is then split into development and held-out documents. Writes data/sample.json.
"""
import collections
import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = 20261009          # the day the population was frozen
TOTAL, FLOOR, DEV_SHARE = 50, 4, 0.4


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
    picked.sort(key=lambda r: (r["split"], r["id"]))
    out = {"seed": SEED, "population": len(pop), "usable": len(usable),
           "per_tag": {t: {"population": len(by_tag[t]), "drawn": quota[t]} for t in tags}, "documents": picked}
    with open(ROOT / "data" / "sample.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    for t in tags:
        print(f"  {t:18} population {len(by_tag[t]):4}  drawn {quota[t]:3}")
    print(f"{len(picked)} drawn from {len(usable)} usable of {len(pop)}: "
          f"{sum(r['split'] == 'dev' for r in picked)} dev, {sum(r['split'] == 'holdout' for r in picked)} held out")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
