"""Draw a second held-out set, for release run 2, from the notifications the first draw didn't pick.

    python -m scripts.draw_holdout2

Release run 1 failed and the fixes were made after reading its errors, so a release claim needs notifications
the system has never been scored on. Same population (1 April to 7 October 2026), same title tags, a new seed,
at least FLOOR per tag. Every document drawn is held out (split "holdout2"); it is labelled by hand, the
configuration is frozen in git, then it is run once. Appends to data/sample.json's documents.
"""
import collections
import json
import pathlib
import random

from scripts.draw_sample import ROOT, title_tag

SEED2 = 20261010       # the day after the first draw
TOTAL, FLOOR = 20, 2


def main() -> int:
    sample = json.loads((ROOT / "data" / "sample.json").read_text(encoding="utf-8"))
    if any(d["split"] == "holdout2" for d in sample["documents"]):
        print("holdout2 already drawn")
        return 1
    taken = {d["id"] for d in sample["documents"]}
    pop = [json.loads(line) for line in (ROOT / "data" / "population.jsonl").read_text(encoding="utf-8").splitlines()]
    left = [r for r in pop if r.get("pdf") and r.get("title") and not r.get("error") and r["id"] not in taken]
    by_tag = collections.defaultdict(list)
    for r in left:
        by_tag[title_tag(r)].append(r)
    tags = sorted(by_tag)
    quota = {t: min(FLOOR, len(by_tag[t])) for t in tags}
    rest = TOTAL - sum(quota.values())
    pool = sum(len(by_tag[t]) - quota[t] for t in tags)
    for t in tags:
        quota[t] += (len(by_tag[t]) - quota[t]) * rest // pool if pool else 0
    for t in sorted(tags, key=lambda t: -len(by_tag[t])):
        if sum(quota.values()) >= TOTAL:
            break
        if quota[t] < len(by_tag[t]):
            quota[t] += 1
    rng = random.Random(SEED2)
    picked = []
    for t in tags:
        for r in rng.sample(sorted(by_tag[t], key=lambda r: r["id"]), quota[t]):
            picked.append({"id": r["id"], "tag": t, "split": "holdout2", "title": r["title"], "rbi_no": r.get("rbi_no"),
                           "date": r.get("date"), "url": r["url"], "pdf": r["pdf"]})
    picked.sort(key=lambda r: r["id"])
    sample["documents"] += picked
    sample["holdout2"] = {"seed": SEED2, "drawn_from": len(left),
                          "per_tag": {t: {"left": len(by_tag[t]), "drawn": quota[t]} for t in tags}}
    with open(ROOT / "data" / "sample.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
        f.write("\n")
    for t in tags:
        print(f"  {t:18} left {len(by_tag[t]):4}  drawn {quota[t]:3}")
    print(f"{len(picked)} drawn for holdout2 from {len(left)} not drawn before")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
