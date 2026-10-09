import datetime as dt

from radar import checks, entities, rules
from radar.llm import select_pages
from radar.text import add_months, dates_in, find_quote, issue_date, parse_date, relative_date

D = dt.date


def test_parse_dates_in_rbi_formats():
    assert parse_date("April 1, 2027") == D(2027, 4, 1)
    assert parse_date("1st April 2027") == D(2027, 4, 1)
    assert parse_date("01.04.2027") == D(2027, 4, 1)          # day first
    assert parse_date("Sept 30, 2026") == D(2026, 9, 30)
    assert dates_in("on or before June 30, 2027 and by 31 March, 2030") == [D(2027, 6, 30), D(2030, 3, 31)]


def test_relative_and_month_end_dates():
    assert relative_date("effective six months from the date of this circular", D(2026, 4, 9)) == D(2026, 10, 9)
    assert relative_date("within 30 days from the date of issue", D(2026, 1, 1)) == D(2026, 1, 31)
    assert add_months(D(2026, 8, 31), 1) == D(2026, 9, 30)


def test_quote_matching_ignores_spacing_and_hyphen_breaks():
    pages = ["intro", "These Directions shall be applicable to Urban Co- operative Banks (hereinafter UCBs)."]
    assert find_quote("applicable to Urban Co-operative Banks", pages) == 2
    assert find_quote("applicable to Urban Co-operative Banks", pages, page=1) == 2   # wrong page is corrected
    assert find_quote("short", pages) is None                                          # too short to count
    assert find_quote("applicable to Rural Co-operative Banks", pages) is None


def test_entity_words_class_phrases_and_exclusions():
    assert entities.named_in("Chief Executive Officer All Banks Madam") == set(entities.BANKS)
    assert entities.named_in("All Scheduled Commercial Banks (excluding Regional Rural Banks)") == {"commercial_banks"}
    assert entities.named_in("all Payment System Providers and Payment System Participants") == set(entities.PAYMENTS)
    assert entities.named_in("Non- Banking Financial Companies") == {"nbfcs"}
    assert entities.named_in("To All Authorised Dealers") == {"authorised_dealers"}
    assert not entities.supports("The bank shall formulate a policy", "nbfcs")


def test_rules_read_title_addressee_and_commencement():
    pages = ["RBI/2026-27/25 DOR.STR.REC.13/07-01-001/2026-27 April 27, 2026 Reserve Bank of India "
             "(Commercial Banks – Credit Facilities) Second Amendment Directions, 2026 Please refer to the Directions. "
             "These Amendment Directions shall come into force from April 1, 2027."]
    r = rules.read(pages, "Reserve Bank of India (Commercial Banks – Credit Facilities) Second Amendment Directions, 2026",
                   issue_date(pages))
    assert {a["type"] for a in r["applies_to"]} == {"commercial_banks"}
    assert r["kind"]["value"] == "amendment"
    assert r["effective_date"]["value"] == "2027-04-01"
    circular = ["RBI/2026-27/283 DoR.RET.REC.239/12.01.001/2026-27 October 07, 2026 All banks, Madam / Sir, "
                "Penal Interest. The Bank Rate is revised to 5.75 per cent with immediate effect."]
    r = rules.read(circular, "Penal Interest on shortfall in CRR and SLR requirements", issue_date(circular))
    assert {a["type"] for a in r["applies_to"]} == set(entities.BANKS)
    assert r["effective_date"]["value"] == "2026-10-07"
    assert r["kind"]["value"] == "rates_operational"


PAGES = ["RBI/2026-27/9 X October 01, 2026 All Primary Dealers Madam / Sir, Title. "
         "These directions shall come into effect from November 1, 2026. "
         "Primary dealers shall submit the return on or before December 15, 2026."]


def _answer(**kw):
    a = {"applies_to": [{"entity_type": "primary_dealers", "quote": "All Primary Dealers Madam", "page": 1}],
         "kind": "new_direction", "action_required": "yes", "action": "Submit the return.",
         "action_quote": "Primary dealers shall submit the return", "action_page": 1,
         "effective_date": {"date": "2026-11-01", "quote": "shall come into effect from November 1, 2026", "page": 1},
         "comply_by": [{"date": "2026-12-15", "what": "return", "quote": "shall submit the return on or before December 15, 2026", "page": 1}],
         "comments_by": {"date": "none", "quote": "", "page": 0}, "amends": "none"}
    a.update(kw)
    return a


def test_checks_accept_quoted_claims():
    m = checks.from_model(_answer(), PAGES, D(2026, 10, 1))
    assert m["applies_to"][0]["verified"]
    assert m["effective_date"]["verified"] and m["comply_by"][0]["verified"]
    p = checks.prediction(checks.card("checked", rules.read(PAGES, "Title", D(2026, 10, 1)), m))
    assert p["effective_date"] == "2026-11-01" and p["comply_by"] == {"2026-12-15"}


def test_checks_reject_unsupported_claims():
    m = checks.from_model(_answer(
        applies_to=[{"entity_type": "nbfcs", "quote": "All Primary Dealers Madam", "page": 1}],          # doesn't name NBFCs
        effective_date={"date": "2026-10-01", "quote": "RBI/2026-27/9 X October 01, 2026", "page": 1},   # letterhead date
        comply_by=[{"date": "2027-01-31", "what": "x", "quote": "Primary dealers shall submit the return", "page": 1}],
    ), PAGES, D(2026, 10, 1))
    assert not m["applies_to"][0]["verified"]
    assert not m["effective_date"]["verified"]
    assert not m["comply_by"][0]["verified"]
    p = checks.prediction(checks.card("checked", rules.read(PAGES, "Title", D(2026, 10, 1)), m))
    assert p["applies_to"] == set() and p["effective_date"] == "withheld" and p["comply_unverified"]


def test_union_keeps_rule_types_and_quoted_rule_dates():
    rr = rules.read(PAGES, "Title", D(2026, 10, 1))
    m = checks.from_model(_answer(applies_to=[],     # the model's date quote doesn't say it's a commencement
                                  effective_date={"date": "2026-12-15", "quote": "shall submit the return on or before December 15, 2026", "page": 1}),
                          PAGES, D(2026, 10, 1))
    c = checks.card("union", rr, m)
    assert {a["type"] for a in c["applies_to"]} == {"primary_dealers"}
    assert c["effective_date"]["value"] == "2026-11-01" and c["effective_date"]["status"] == "verified"


def test_union_withholds_when_verified_dates_disagree():
    pages = [PAGES[0] + " The amended limits come into effect from December 15, 2026."]
    rr = rules.read(pages, "Title", D(2026, 10, 1))
    m = checks.from_model(_answer(effective_date={"date": "2026-12-15", "page": 1,
                                                  "quote": "The amended limits come into effect from December 15, 2026"}),
                          pages, D(2026, 10, 1))
    assert m["effective_date"]["verified"] and rr["effective_date"]["value"] == "2026-11-01"
    c = checks.card("union", rr, m)
    assert c["effective_date"]["status"] == "check" and checks.prediction(c)["effective_date"] == "withheld"


def test_page_selection_keeps_first_pages_and_deadlines():
    pages = ["p"] * 60
    pages[40] = "Returns shall be submitted to RBI by June 30, 2027"
    pages[10] = "These Directions shall come into force on April 1, 2027"
    keep = select_pages(pages, max_pages=6)
    assert keep[:3] == [1, 2, 3] and 11 in keep and 41 in keep
