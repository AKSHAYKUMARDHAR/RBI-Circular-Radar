# Label guide

How each RBI notification is labelled. The labels are the answer key for the evaluation, so they are
written from the document alone, before any extraction prompt exists, and the held-out labels are never
changed after a run. Mistakes found later are logged at the end of this file, not fixed in place.

Every labelled value carries the **exact quote** that supports it and the **PDF page** (1 = the first
page of the file). `python -m eval.check_labels` confirms each quote is on its page, comparing letters
and digits only.

## The fields

| Field | Values | Scored as |
| --- | --- | --- |
| `applies_to` | a set of entity types (below) | per (notification, entity type) pair: recall and precision |
| `kind` | `new_direction`, `amendment`, `withdrawal`, `draft`, `rates_operational`, `clarification`, `other` | accuracy |
| `action_required` | `yes`, `no` | accuracy |
| `effective_date` | an ISO date, or `not_stated` | correct / wrong / withheld |
| `comply_by` | a set of ISO dates, or `none` | as a set: correct / wrong / withheld |
| `comments_by` | an ISO date, or `none` | correct / wrong / withheld |
| `amends` | the short title of the Master Direction it amends, or `none` | shown, not scored |

## Entity types

Seventeen types: RBI's eleven types of regulated entity, the payment-system and market participants a
fintech meets, and a catch-all.

| Key | Who | Typical wording |
| --- | --- | --- |
| `commercial_banks` | Scheduled and non-scheduled commercial banks, including foreign banks in India | "Commercial Banks", "All Scheduled Commercial Banks" |
| `small_finance_banks` | Small finance banks | "Small Finance Banks" |
| `payments_banks` | Payments banks | "Payments Banks" |
| `regional_rural_banks` | Regional rural banks | "Regional Rural Banks" |
| `local_area_banks` | Local area banks | "Local Area Banks" |
| `urban_coop_banks` | Primary (urban) co-operative banks | "Urban Co-operative Banks", "UCBs" |
| `rural_coop_banks` | State and central co-operative banks | "Rural Co-operative Banks", "StCBs", "DCCBs" |
| `aifis` | All-India financial institutions (EXIM Bank, NABARD, NHB, SIDBI, NaBFID) | "All India Financial Institutions" |
| `nbfcs` | Non-banking financial companies, all layers, including housing finance companies | "Non-Banking Financial Companies", "NBFCs", "HFCs" |
| `arcs` | Asset reconstruction companies | "Asset Reconstruction Companies" |
| `cics` | Credit information companies | "Credit Information Companies" |
| `payment_aggregators` | Payment aggregators and gateways, online, physical and cross-border | "Payment Aggregators", "PA-CB" |
| `ppi_issuers` | Issuers of prepaid payment instruments (wallets, prepaid cards) | "PPI Issuers", "Prepaid Payment Instruments" |
| `payment_operators` | Other payment system operators and participants: card networks, ATM and white-label ATM operators, BBPOUs, TReDS, NPCI | "Payment System Operators", "Card Networks" |
| `authorised_dealers` | Authorised persons under FEMA: AD banks, full-fledged money changers | "All Category-I Authorised Dealer banks", A.P. (DIR Series) circulars |
| `primary_dealers` | Primary dealers | "All Primary Dealers" |
| `other` | Anyone else addressed: LAF participants, market participants, government agencies, the public | "All LAF participants", "All market participants" |

## Rules

1. **Applies to = who must act on it or whose rules it changes.** Read, in order: the title (since the
   2025 consolidation, directions name their entity type: "Reserve Bank of India (Payments Banks –
   ...) Directions"), the addressee line ("All banks", "All Primary Dealers"), and any applicability
   paragraph. Label every type the document names; nothing it doesn't.
2. **"All banks" means all seven bank types** (commercial, small finance, payments, regional rural,
   local area, urban co-operative, rural co-operative) unless the text narrows it ("All Scheduled
   Commercial Banks (excluding Regional Rural Banks)"). Follow the narrowing exactly.
3. **A circular to banks in a role is labelled with the role.** A.P. (DIR Series) circulars to
   authorised dealer banks are `authorised_dealers`; a circular to "banks acting as sponsor banks for
   BBPS" is `payment_operators` plus the bank types it names. Don't add bank types the text doesn't name.
4. **Drafts and withdrawals apply to whoever the final or withdrawn instructions cover.**
5. **Kind.** `amendment`: changes an existing direction ("Amendment Directions", "amended as under").
   `new_direction`: a new set of directions or a new framework. `withdrawal`: withdraws or repeals
   instructions. `draft`: issued for comments. `rates_operational`: policy-rate changes, auction and
   facility notices, reporting procedures and routine operational announcements. `clarification`: FAQs,
   clarifications, corrigenda. `other`: anything else, including updates to sanctions lists circulated
   under UAPA and consolidations of earlier instructions.
6. **Action required = yes** when the notification creates or changes something a named entity must
   do, stop doing, report, disclose, or a limit it must meet. Rate changes that change what an entity
   pays or charges are `yes`. Drafts, pure information, permissions ("may") and exemptions are `no`.
   A Master Direction that consolidates instructions still states obligations and is `yes`; a notice
   that only announces a consolidation, or lists withdrawn circulars, is `no`. A repeal that replaces
   rules with new ones from a date is `yes`.
7. **Dates.**
   - `effective_date`: when the instructions come into force. "With immediate effect" or "come into
     force on the date of issue" is the notification's date. If no date is given, `not_stated`.
   - `comply_by`: every date by which a named entity must have done something (submit a return,
     put a system in place, complete a review). Not the effective date unless the text sets it as
     a deadline. If none, `none`.
   - `comments_by`: the last date for comments on a draft. If none, `none`.
   - "From the date of issue" is the notification's date, like "with immediate effect".
   - A date given only by reference ("three months from the date of this circular") is computed and
     the label note says so.
   - A recurring deadline ("by the 10th of the following month") is not a date: `comply_by` stays
     empty and the note records it.
8. **Payment-system wording.** Payment aggregators, PPI issuers and other payment system operators
   are all authorised under the Payment and Settlement Systems Act, so a document addressed to the
   general class ("Payment System Providers", "an entity authorised to operate a payment system under
   the PSS Act") is labelled with all three: `payment_operators`, `payment_aggregators`, `ppi_issuers`.
   A document about one named system ("TReDS Platform Operators") gets only that system's type.
   "Participants" adds no bank or NBFC type unless the text names it.
9. **Undecidable is skipped.** If the document can't settle a field (it points to an annexe that isn't
   in the PDF, for example), the field is `skip`, with the reason, and left out of scoring.

## Sampling

The population is every notification on RBI's site from 1 April to 7 October 2026 (notification ids
13360 to 13735). Each is tagged with a kind from its title alone, and a seeded random draw, stratified
by kind, picks the evaluation set, then splits it into development and held-out halves. The seed, the
population list and the draw are committed before any document is labelled.

**Payments supplement.** The random draw picked no notification on payment systems, so no payment
aggregator or PPI issuer appeared in either answer key, though those are licences the product is pitched
at. Before any prompt existed, every other notification that regulates payments was added as its own
stratum by a rule applied to the population list: issued by the Department of Payment and Settlement
Systems, or titled "digital payment", "payment system" or "non-bank entities". That added 10
notifications (4 development, 6 held-out, split with their own seed). They are flagged `supplement` in
`documents.json` and results are reported for them separately, since they weren't drawn at random.
Rule 8 was written at the same time, before these were labelled.

## Changes after a run

None yet.
