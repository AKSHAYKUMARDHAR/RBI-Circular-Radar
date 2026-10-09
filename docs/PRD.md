# PRD: "RBI Circular Radar" — which new RBI rules apply to you, what to do, and by when

Author: Akshay Dhar · Status: draft v1 · 9 October 2026

## TL;DR

The Reserve Bank of India publishes a new notification almost every working day, often several. On
7 October 2026 alone it issued ten, and its numbering for the year had reached RBI/2026-27/289. A
fintech's compliance team (a payment aggregator, a wallet issuer, a digital lender) has to read every
one, decide whether it applies to their licences, and pull out what must change and by when. Most of
it doesn't apply. The few that do carry penalties when missed.

RBI Circular Radar reads each new notification, says which types of regulated entity it applies to,
whether it requires action, and the dates that matter (in force from, comply by, comments due by),
each with the exact words and page from RBI's own document. A team picks its licences once and gets
a daily digest of only what applies to it, with a mark-as-reviewed step that leaves an audit trail.

**The error that matters most here is a miss.** A notification that applies to you, filed as
irrelevant, is how penalties happen. So the release gate is recall-first: no applicable notification
missed on a held-out set of real RBI notifications, frozen and labelled before any prompt is written.

## Problem and evidence

**The volume is high and growing.** RBI's notifications feed showed ten items on 7 October 2026
alone, numbered up to RBI/2026-27/289 six months into the financial year, roughly 580 a year at that
pace ([RBI notifications RSS](https://www.rbi.org.in/notifications_rss.xml)). An academic study puts
the yearly flow of circulars above 200 across KYC/AML, digital lending, cybersecurity and risk, and
calls manual interpretation "a significant bottleneck"
([IJRASET](https://www.ijraset.com/research-paper/an-integrated-nlp-pipeline-for-automated-regulatory-impact)).

**The rulebook was just rebuilt, so the work changed shape.** In November 2025 RBI withdrew about
9,000 circulars and consolidated them into 244 Master Directions, issued separately for each type of
regulated entity ([Business Today](https://www.businesstoday.in/amp/latest/economy/story/rbi-consolidates-9000-circulars-into-244-master-directions-for-enhanced-ease-of-doing-business-details-here-504215-2025-11-28)).
New rules now arrive as "Amendment Directions" to those, often the same change issued several times,
once per entity type: on 7 October 2026 one capital-adequacy change came as four documents, for
commercial banks, small finance banks, payments banks and all-India financial institutions. Working
out "does this one apply to us" is now a filtering problem across many near-identical documents.

**Missing one costs money and trust.** RBI fined Cashfree Payments, a payment aggregator, ₹3.10 lakh
in March 2026 for non-compliance with its payment aggregator directions
([Moneylife](https://www.moneylife.in/article/rbi-slaps-310-lakh-penalty-on-cashfree-payments-india/79960.html)),
three NBFCs ₹12 lakh in August 2026 for KYC and fair-practice lapses
([Moneylife](https://www.moneylife.in/article/rbi-slaps-12-lakh-penalty-on-3-nbfcs-for-compliance-lapses/81300.html)),
and Hero FinCorp, Ola Financial Services and KLM Axiva ₹15.80 lakh in September 2026
([Moneylife](https://www.moneylife.in/article/hero-fincorp-ola-financial-services-and-klm-axiva-fined-1580-lakh-by-rbi/81761.html)).
The fines are small; the supervisory findings, show-cause notices and repeat inspections behind them
are not.

**RBI itself asks for tooling.** Its January 2024 circular (RBI/2023-24/117) told banks and
middle- and upper-layer NBFCs to move compliance monitoring onto technology, with escalation, an
audit trail and a dashboard for senior management
([ClearTax](https://cleartax.in/s/internal-compliance-monitoring-rbi-circular-117)); the deadline was
later extended to 30 April 2025
([Complinity](https://complinity.com/blog/compliance/rbi-extends-deadline-to-implement-workflow-based-solution/)).
Yet vendors report that many entities still get regulatory updates "pushed via excels"
([Lawrbit](https://www.lawrbit.com/article/rbi-regulated-entities-banks-nbfcs-hfcs-cics-implement-futuristic-scalable-compliance-management-solution/)).

**Fintech rules are moving fast right now.** Consolidated directions for payment aggregators came in
September 2025, with authorisation deadlines that ran to December 2025
([AZB & Partners](https://www.azbpartners.com/bank/rbi-issues-consolidated-reserve-bank-of-india-regulation-of-payment-aggregators-directions-2025/));
a draft master direction on prepaid payment instruments followed in April 2026
([RBI](https://www.rbi.org.in/scripts/bs_viewcontent.aspx?Id=4987)); a vendor reports recovery rules
for lending apps taking effect on 1 January 2027
([eCorpIT](https://ecorpit.com/ecorpit-rbi-device-locking-recovery-compliance-engineering-service-india-2026/),
to be checked against the RBI text).

## Users and jobs to be done

- **Compliance manager at a fintech** (payment aggregator, PPI issuer, NBFC digital lender). A
  BharatPe job posting describes the work: monitor circulars from RBI, NPCI and others, run impact
  assessments, coordinate with product, legal and tech
  ([NodeFlair](https://nodeflair.com/jobs/bharatpe-senior-manager-compliance-testing-539452)).
  *"Tell me every morning which new RBI items apply to our licences, what we must do, and by when,
  so I can assign them before anyone asks."*
- **Head of compliance / principal officer.** *"Show me that nothing applicable was missed, and who
  reviewed what."* Needs the audit trail RBI's 2024 circular expects.
- **Product or engineering lead at a fintech.** *"When a rule changes something we built, tell me
  the clause and the date, not a summary."*

Out of scope for v1: banks' large compliance departments (they buy TeamLease-class suites), legal
interpretation, and non-RBI regulators (NPCI, SEBI, IRDAI).

## Competitive landscape and positioning

| Option | What it does | Gap the Radar fills |
| --- | --- | --- |
| Reading rbi.org.in or the RSS feed | Complete and free | Every item, every entity type; no filtering, no dates pulled out |
| Law-firm and consultant newsletters | Expert commentary | Weekly or monthly, after the fact; not tied to your licences |
| Compliance suites (TeamLease RegTrack, Fintellix C-Trac, Complinity) | Obligation registers, maker-checker workflows, reminders ([TeamLease](https://teamleaseregtech.com/product-services/statutory-regulatory-compliance-management-software/), [Fintellix](https://fintellix.com/rbis-compliance-mandate-is-live-compliance-tracker-c-trac-has-you-covered/)) | Priced and built for enterprises; their AI claims aren't independently evaluated |
| Research prototypes (autoReg) | Summaries and change detection on 75 circulars, F1 0.78 ([IJRASET](https://www.ijraset.com/research-paper/an-integrated-nlp-pipeline-for-automated-regulatory-impact)) | Not a product; no applicability or deadline focus |

Positioning: **free, fintech-first, and measured.** Every claim is quoted from RBI's PDF, and the
accuracy is published from a held-out test on real notifications, misses first.

## Goals and non-goals

Goals
1. Tell a fintech team, for each new RBI notification, whether it applies to their entity types, with
   the words that say so.
2. Pull out the dates that matter (in force from, comply by, comments due by), each quoted.
3. Classify what the notification is (new direction, amendment, withdrawal, draft for comments,
   rate or operational change) and whether it requires action.
4. Make review traceable: reviewed, not applicable (with a reason), or assigned, with an exportable log.

Non-goals
- Legal advice or interpretation of what a rule means for a specific business.
- Summarising whole Master Directions; v1 reads new notifications.
- Other regulators, and authenticated sources (RBI's DAKSH portal, bank-specific letters).

## MVP scope

1. **Feed watcher.** Reads RBI's notifications RSS daily (a scheduled job), downloads each new
   notification's official PDF and keeps its hash.
2. **Reader.** For each notification: entity types it applies to, kind, action required or not,
   key dates, and the Master Direction it amends, each with quote and page.
3. **Profile.** The team ticks its entity types once (for example "NBFC" and "Payment aggregator").
4. **Digest.** A page of new notifications, those that apply first, sorted by the nearest date, each
   with its quotes and a link to the RBI PDF; everything else one click away, never hidden.
5. **Review.** Mark reviewed, not applicable (reason required) or assigned to a name; export the log
   as CSV. Stored in the browser for the demo.

Delivery: a static site rebuilt daily by GitHub Actions, so there is no server to keep awake, and the
notifications the Radar has read are public data.

## How answers stay trustworthy

**The rules read what is structured; the model reads the rest; code checks both.**

1. **Rules first.** Since the 2025 consolidation, most directions name their entity type in the
   title ("Reserve Bank of India (Payments Banks – Prudential Norms on Capital Adequacy) Third
   Amendment Directions, 2026"), and circulars open with an addressee line ("All banks", "All
   Primary Dealers"). Code maps these to entity types with a fixed dictionary.
2. **The model reads the PDF** and returns the same fields with an exact quote and page for each.
3. **Code checks every claim.** A quote must be found on its page; a date must appear in its quote;
   an entity type must be named in its quote.
4. **When the rules and the model disagree on who a notification applies to, the Radar shows both
   (the union).** A false alert costs a reader one minute; a missed one can cost a penalty.
5. **Nothing is hidden.** Notifications judged not applicable stay listed below the applicable ones,
   with the reason, so a person can overrule the Radar.

## Safety, privacy and compliance

- Public documents only; no customer, employee or transaction data is processed.
- Every card says it is not legal advice and links the RBI original, which prevails.
- The review log stays in the user's browser in v1.
- The model never sees anything but RBI's own text; a prompt-injection check runs on every document
  anyway, as in the earlier projects.

## Success metrics

North star: **applicable notifications missed: 0.**

| Metric | Target | How measured |
| --- | --- | --- |
| Applicable (notification, entity type) pairs missed | 0 on the held-out set | Eval against hand labels |
| Applicability precision | ≥ 85% | Eval; alert fatigue is the cost |
| Wrong dates shown | ≤ 2% of labelled dates | Eval |
| Correct dates shown | ≥ 85% of labelled dates | Eval |
| Kind and "action required" correct | ≥ 90% | Eval |
| Time from RBI publication to digest | < 24 hours | Feed timestamps vs build log |
| Triage time per notification | from ~10 minutes to ~1 | Timed on 10 notifications, by me, before and after |

## Evaluation plan

**Documents, frozen before any prompt.** About 50 real RBI notifications from April to October 2026,
chosen to cover every kind: entity-wise amendment directions, NBFC and payment-system items, foreign
exchange circulars to authorised dealers, rate and operational notices, drafts for comments and
withdrawals. Each is pinned by URL and SHA-256. A seeded random draw, stratified by kind, splits them
into about 20 for development and 30 held out.

**Answer keys, written by hand before any prompt exists**, under a label guide written first: for
each notification, the set of entity types it applies to (14 types: RBI's 11 regulated-entity types
plus payment aggregators, PPI issuers and other payment system operators, with authorised dealers and
primary dealers), its kind, whether action is required, and its dates, each with quote and page,
checked against the PDF by a script.

**Scoring.**
- Applicability, per (notification, entity type) pair: recall and precision. A miss is the costly error.
- Dates: correct, wrong (a date shown that the document doesn't support, or the wrong one), or
  withheld.
- Kind and action required: accuracy.
- Every version is scored from the same model answers: rules only, model only, model + checks, and
  rules + model (union), so the value of each layer is measured, not assumed.

**Release gate** (held-out set, run once): 0 applicable pairs missed, precision ≥ 85%, wrong dates
≤ 2%, correct dates ≥ 85%, every shown claim quoted and verified.

**Free-tier plan.** Notifications are short (1–10 pages), so the dev runs compare gemini-3.5-flash-lite
(500 free requests a day) with gemini-3.5-flash (20 a day). The cheaper model ships if it passes the
dev bar; one read per document is tested against two. Earlier projects showed the lite models failing
on long policy wordings; this checks whether that holds on short, structured documents.

## Launch and distribution plan

- Live demo: a public digest page, rebuilt daily, with a profile picker.
- Share in fintech compliance communities and with two or three practitioners for a 15-minute test,
  timing their triage with and without the Radar.
- Case study and PRD on the portfolio, with the held-out results, pass or fail.

## Timeline and risks

| Days | Work |
| --- | --- |
| 1 | Research, PRD, repo |
| 2–3 | Label guide, freeze ~50 notifications, write answer keys |
| 3–5 | Feed watcher, rules, reader, checks, digest page |
| 5–6 | Dev runs (lite vs flash, one read vs two), fixes on dev only |
| 7 | Held-out release run, once |
| 8 | Deploy, write-up, portfolio |

Risks
- **RBI changes its site or feed.** The fetcher pins URLs and hashes; the scheduled job fails loudly.
- **"Applies to" is ambiguous** ("All banks" vs specific bank types). The label guide fixes the
  mapping before labelling; the union rule biases toward recall.
- **Free-tier limits and outages.** Retries count against the daily quota, as the last project found;
  retries are capped and a document the provider never served is left out of the scores, not counted.
- **Labelling errors.** One labeller (me). Held-out keys never change after a run; mistakes found
  later are logged, not fixed.

## Open questions

- Should the digest also go out by email or Slack (needs a mail service) or stay a page?
- Should v2 read the Master Directions themselves, to answer "what does the current rule say"?
- Which fintech profiles matter most to test with users: PA, PPI or NBFC digital lending?

## Sources

- RBI notifications RSS feed, read 9 October 2026: https://www.rbi.org.in/notifications_rss.xml
- Business Today on the consolidation into 244 Master Directions (November 2025):
  https://www.businesstoday.in/amp/latest/economy/story/rbi-consolidates-9000-circulars-into-244-master-directions-for-enhanced-ease-of-doing-business-details-here-504215-2025-11-28
- Moneylife on RBI penalties (Cashfree, March 2026; NBFCs, August and September 2026):
  https://www.moneylife.in/article/rbi-slaps-310-lakh-penalty-on-cashfree-payments-india/79960.html,
  https://www.moneylife.in/article/rbi-slaps-12-lakh-penalty-on-3-nbfcs-for-compliance-lapses/81300.html,
  https://www.moneylife.in/article/hero-fincorp-ola-financial-services-and-klm-axiva-fined-1580-lakh-by-rbi/81761.html
- ClearTax on RBI/2023-24/117 (technology for compliance monitoring):
  https://cleartax.in/s/internal-compliance-monitoring-rbi-circular-117
- Complinity on the deadline extension:
  https://complinity.com/blog/compliance/rbi-extends-deadline-to-implement-workflow-based-solution/
- Lawrbit on updates still pushed via spreadsheets:
  https://www.lawrbit.com/article/rbi-regulated-entities-banks-nbfcs-hfcs-cics-implement-futuristic-scalable-compliance-management-solution/
- IJRASET, autoReg (NLP pipeline for RBI circulars):
  https://www.ijraset.com/research-paper/an-integrated-nlp-pipeline-for-automated-regulatory-impact
- AZB & Partners on the 2025 payment aggregator directions:
  https://www.azbpartners.com/bank/rbi-issues-consolidated-reserve-bank-of-india-regulation-of-payment-aggregators-directions-2025/
- RBI draft Master Direction on PPIs, 2026: https://www.rbi.org.in/scripts/bs_viewcontent.aspx?Id=4987
- eCorpIT on recovery rules for lending apps (vendor source):
  https://ecorpit.com/ecorpit-rbi-device-locking-recovery-compliance-engineering-service-india-2026/
- NodeFlair, BharatPe compliance job posting:
  https://nodeflair.com/jobs/bharatpe-senior-manager-compliance-testing-539452
- TeamLease RegTech and Fintellix product pages:
  https://teamleaseregtech.com/product-services/statutory-regulatory-compliance-management-software/,
  https://fintellix.com/rbis-compliance-mandate-is-live-compliance-tracker-c-trac-has-you-covered/
