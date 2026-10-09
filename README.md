# RBI Circular Radar

Which new Reserve Bank of India notifications apply to you, what to do, and by when. It checks RBI every 10
minutes; for each new notification it says which of 17 entity types it applies to (banks by type, NBFCs, payment
aggregators, PPI issuers, authorised dealers and more), whether it requires action, and the dates that matter.
Every claim carries RBI's own words and the page they're on.

**Live digest: https://akshaykumardhar.github.io/RBI-Circular-Radar/**. Tick your entity types, filter
to "action required", export to CSV.

- Product requirements: [docs/PRD.md](docs/PRD.md)
- Every evaluation run, with its errors: [eval/RUNS.md](eval/RUNS.md)
- How the answer keys were written: [data/LABEL_GUIDE.md](data/LABEL_GUIDE.md)

## Results

Tested on real RBI notifications, frozen and labelled by hand before any prompt existed. Scoring is per
(notification, entity type) pair, and the release gate was recall-first: **no applicable pair missed**,
precision ≥ 85%, wrong dates ≤ 2%, correct dates ≥ 85%.

| Run | Notifications | Missed pairs | Precision | Dates correct / wrong / withheld | Gate |
| --- | --- | --- | --- | --- | --- |
| Release run 1 | 35 held out | 2 of 59 | 95.0% | 99 / 0 / 6 | **failed** |
| Release run 2 (fresh draw) | 20 held out | 1 of 51 | 100% | 51 / 1 / 8 | **failed** |

**Blocked twice, both times by one or two misses.** Two of the three misses were correct model answers that
my own entity check discarded: "Liquidity Adjustment Facility (LAF) participants" and "Lead Banks Concerned"
weren't in its word list. The third was real: third-party remittance platforms named only in an annex.
The date checks worked. On its own the model got 11 of 165 dates wrong; after the checks, 1 was wrong
(from the rules), and the rest were shown as "check the document".

The shipped version changes one thing: an entity type the model names but the check can't confirm is
shown as **"may apply: check"**, not dropped. Re-scored on the same cached answers, it misses 1 pair in 110
with no wrong dates. That's measured after the fact, so it isn't a pass. The live digest is the next test.

## How it works

1. **Rules** read what RBI's format makes reliable: the entity type in a direction's title ("Reserve Bank of
   India (Payments Banks – ...) Directions"), the addressee line ("All banks"), the applicability and
   commencement sentences, and A.P. (DIR Series) circulars, which go to authorised dealers.
2. **One gemini-3.5-flash-lite read** per notification. It gets the pages that matter (up to 18 of up to 83) and
   returns JSON: entity types, kind, action, dates, each with an exact quote and page.
3. **Code checks every claim.** The quote must be on the cited page of the PDF and must support the claim:
   - an entity's quote must name it, or a class that covers it ("All banks", "Payment System Providers");
   - a date's quote must contain the date and say what it's for, so a letterhead date isn't accepted as a
     commencement date.
4. **Merge.** Entity types come from either reader. Dates are shown where the readers agree or one is verified,
   and withheld where they disagree.

Ablation, development set (25 notifications):

| Version | Missed pairs | Dates wrong |
| --- | --- | --- |
| rules only | 0 | 6 |
| model only | 1 | 5 |
| model + checks | 2 | 1 |
| rules + model | 0 | 0 |

On held-out data, the rules scored worse than on development, because they were written after reading the
development documents. The model, not the rules, carried recall on held-out data.

## Run it

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
echo "GEMINI_API_KEY=..." > .env                      # free key from Google AI Studio; never commit it
python -m scripts.fetch_documents                      # download the 80 evaluation PDFs from RBI, verify hashes
python -m eval.check_labels data/labels_dev.json       # every answer-key quote is on its page
python -m eval.run_eval --split dev --replay 91958b5241    # re-score cached answers, no API calls
python -m radar.digest --new                           # read notifications published since the last run
python -m pytest -q tests
```

The site is static (`site/`), updated by [a GitHub Actions workflow](.github/workflows/digest.yml) that checks RBI every 10 minutes,
reads new notifications with the `GEMINI_API_KEY` repository secret and publishes to GitHub Pages.

Not legal advice. The tool points you to the notification; read it before you act.

Built with Claude Code, after [UPI Triage Agent](https://github.com/AKSHAYKUMARDHAR/UPI-Triage-Agent),
[Is This a Scam?](https://github.com/AKSHAYKUMARDHAR/Is-This-A-Scam) and
[Will My Policy Pay?](https://github.com/AKSHAYKUMARDHAR/Will-My-Policy-Pay).
