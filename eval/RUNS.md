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

## Held-out (35 notifications: 29 random draw + 6 payments supplement)

Not yet run.
