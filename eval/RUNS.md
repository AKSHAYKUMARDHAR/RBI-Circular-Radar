# Evaluation runs

Every run, in order, with what changed between runs. Development runs are for building; the held-out
set is run once, with the configuration frozen in git beforehand. Model answers are cached in
`eval/answers/` and committed, so every score here can be reproduced without a request.

## Development (25 notifications: 21 random draw + 4 payments supplement, 62 applicable pairs, 75 date facts)

**Run 1**: gemini-3.5-flash-lite, one read ([log](results/dev_lite_run1.log)).
Union: 1 missed pair, 100% precision, 68 dates correct, **7 wrong**. Failed on wrong dates.

What went wrong, read from the documents:
- On 4 notifications that never say when they take effect, the model gave the letterhead date as the effective
  date, quoting only the date line ("October 01, 2026"). The check accepted the quote because the date was in it.
- It read a facility's open window (R13469) and an exemption cutoff (R13516) as compliance deadlines.
- One real deadline (R13400, "to be submitted to RBI by June 30, 2027") was on page 78 of 81, which the page
  selection didn't send.
- Foreign portfolio investors (R13464), whose limits changed, weren't recognised as "other".

Changes before run 2, all general rather than per-document:
- A date's quote must say what the date is for: commencement words for an effective date, obligation words
  for a deadline, "comments" for a comment date.
- A deadline found by the rules but not the model is shown as "check", not as fact.
- Page selection sends the first three pages, then commencement and applicability pages, then deadline pages
  (up to 18, from 14).
- The prompt's "other" examples gained foreign portfolio investors, exporters, importers and non-residents
  (and the entity check's word list with them); the prompt says an optional facility or permission is "no
  action" and the letterhead date alone isn't an effective date.

**Run 2**: same model, one read, prompt version `ec58effdcc` ([log](results/dev_lite_run2.log)).

| Version | Missed pairs | Precision | Dates correct / wrong / withheld | Kind | Action |
| --- | --- | --- | --- | --- | --- |
| Rules only | 0 | 100% | 69 / 6 / 0 | 96% | 80% |
| Model only | 1 | 100% | 70 / 5 / 0 | 88% | 88% |
| Model + checks | 2 | 100% | 70 / 1 / 4 | 88% | 88% |
| **Rules + model (union)** | **0** | **100%** | **71 / 0 / 4** | **100%** | **88%** |

The union passes the dev bar. The checks turn 4 of the model's 5 wrong dates into "check the document";
the rules catch the entity types the checks drop. The rules were written by the same person who wrote the
answer keys, after reading the development documents, so their dev score flatters them; the held-out run
is the test.

**Two reads** ([log](results/dev_lite_reads2.log)): a second flash-lite read per document lifts the model's own
recall to 100% but changes nothing in the union (0 missed, 71 / 0 / 4) and lowers action accuracy to 84%
(disagreements default to "yes"). One read ships.

**gemini-3.5-flash not run on dev.** Its free tier allows 20 requests a day, fewer than the 25 development
documents, and the PRD's rule was that the cheaper model ships if it passes the dev bar. It did.

**Frozen for the release run:** rules + gemini-3.5-flash-lite union, one read, prompt version `ec58effdcc`,
up to 18 pages per notification, temperature 0.

## Held-out (35 notifications: 29 random draw + 6 payments supplement, 59 applicable pairs, 105 date facts)

**Release run 1** — frozen configuration from commit 9d453a9, run once ([log](results/holdout_run1.log)).
**Failed the gate: 2 applicable pairs missed (gate: 0).** Every other gate line passed.

| Version | Missed pairs | Precision | Dates correct / wrong / withheld | Kind | Action |
| --- | --- | --- | --- | --- | --- |
| Rules only | 6 | 98.1% | 95 / 10 / 0 | 89% | 77% |
| Model only | 1 | 96.7% | 102 / 3 / 0 | 91% | 91% |
| Model + checks | 2 | 96.6% | 99 / 0 / 6 | 91% | 91% |
| **Rules + model (union)** | **2** | **95.0%** | **99 / 0 / 6** | **97%** | **91%** |

Gate: missed 2 (needed 0) ✗, precision 95.0% (≥ 85%) ✓, wrong dates 0.0% (≤ 2%) ✓, correct dates 94% (≥ 85%) ✓.
Random draw: 1 missed, 94.2% precision. Payments supplement: 1 missed, 100% precision.

Both misses are the catch-all type "other", not a regulated entity type:
- **R13727** (to "All Liquidity Adjustment Facility (LAF) participants"): the model answered correctly, with the
  right quote. **The entity check threw it away**: its word list had "LAF participants", and the "(LAF)" in
  between broke the match. The rules missed the same line for the same reason. A bug in my code, not the model.
- **R13449** (outward remittances through non-bank platforms): the label counts the third-party platforms as
  "other", because the annex places obligations on them ("The third party shall have a comprehensive Privacy
  Policy"). Neither the rules nor the model flagged them; the model listed only the authorised dealers.

On the 16 named entity types (57 pairs), the model and the model + checks missed 0 and added 0; the union
missed 0 and added 1. The rules, which scored 100% on development, missed 4 named pairs here (they were written
after reading the development documents), so on unseen notifications the model carried recall, not the rules.

The 3 extra pairs: two "other" (R13701 names NRIs and FPIs in a KYC proviso; R13712 tells banks to inform their
"exporter constituents"), both let through by the "other" words I added after development run 1; and one
`aifis` from the rules (R13592's applicability sentence mentions the National Housing Bank *Act*).
Dates: none wrong; 6 withheld as "check the document", 3 of them where the notification states no date.

The held-out labels are unchanged. Fixes below are tested on development only, and a release claim needs a
fresh held-out set.
