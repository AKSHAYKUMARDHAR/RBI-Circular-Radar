"""The 17 entity types, the words RBI uses for each, and the class phrases that cover several at once.

Mirrors data/LABEL_GUIDE.md: "All banks" means the seven bank types (rule 2), a payment-system class
phrase means all three payment types (rule 8), A.P. (DIR Series) circulars go to authorised dealers (rule 3).
"""
import re

BANKS = ["commercial_banks", "small_finance_banks", "payments_banks", "regional_rural_banks", "local_area_banks",
         "urban_coop_banks", "rural_coop_banks"]
PAYMENTS = ["payment_operators", "payment_aggregators", "ppi_issuers"]
TYPES = BANKS + ["aifis", "nbfcs", "arcs", "cics"] + PAYMENTS + ["authorised_dealers", "primary_dealers", "other"]

LABELS = {
    "commercial_banks": "Commercial banks",
    "small_finance_banks": "Small finance banks",
    "payments_banks": "Payments banks",
    "regional_rural_banks": "Regional rural banks",
    "local_area_banks": "Local area banks",
    "urban_coop_banks": "Urban co-operative banks",
    "rural_coop_banks": "Rural co-operative banks (StCBs, DCCBs)",
    "aifis": "All-India financial institutions",
    "nbfcs": "NBFCs (including HFCs)",
    "arcs": "Asset reconstruction companies",
    "cics": "Credit information companies",
    "payment_aggregators": "Payment aggregators",
    "ppi_issuers": "PPI issuers (wallets, prepaid cards)",
    "payment_operators": "Other payment system operators (card networks, ATM operators, BBPOUs, TReDS)",
    "authorised_dealers": "Authorised dealers and money changers",
    "primary_dealers": "Primary dealers",
    "other": "Others addressed (market participants, agencies, the public)",
}

# Words that name one type. Matched case-insensitively on text with hyphens and line breaks loosened.
_H = r"[\s\-–]*"          # PDF text often splits "Co- operative", "Non- Banking"
ALIASES = {
    "commercial_banks": [r"\bcommercial banks?\b", r"\bSCBs?\b"],
    "small_finance_banks": [r"\bsmall finance banks?\b", r"\bSFBs?\b"],
    "payments_banks": [r"\bpayments? banks?\b", r"\bPBs\b"],
    "regional_rural_banks": [r"\bregional rural banks?\b", r"\bRRBs?\b"],
    "local_area_banks": [r"\blocal area banks?\b", r"\bLABs?\b"],
    "urban_coop_banks": [rf"\burban co{_H}operative banks?\b", r"\bUCBs?\b", rf"\bprimary \(?urban\)? co{_H}operative banks?\b"],
    "rural_coop_banks": [rf"\brural co{_H}operative banks?\b", rf"\bstate co{_H}operative banks?\b",
                         rf"\bcentral co{_H}operative banks?\b", r"\bStCBs?\b", r"\bDCCBs?\b"],
    "aifis": [r"\ball[\s\-]+india financial institutions?\b", r"\bAIFIs?\b", r"\bEXIM Bank\b", r"\bNABARD\b",
              r"\bSIDBI\b", r"\bNaBFID\b", r"\bNational Housing Bank\b"],
    "nbfcs": [rf"\bnon{_H}banking financial compan(?:y|ies)\b", r"\bNBFCs?\b", r"\bhousing finance compan(?:y|ies)\b", r"\bHFCs?\b"],
    "arcs": [r"\basset reconstruction compan(?:y|ies)\b", r"\bARCs?\b"],
    "cics": [r"\bcredit information compan(?:y|ies)\b", r"\bCICs?\b"],
    "payment_aggregators": [r"\bpayment aggregators?\b", r"\bPA-CB\b", r"\bPAs\b", r"\bpayment gateways?\b"],
    "ppi_issuers": [r"\bPPI issuers?\b", r"\bprepaid payment instruments?\b", r"\bPPIs?\b"],
    "payment_operators": [r"\bcard networks?\b", r"\bwhite[\s\-]+label ATM operators?\b", r"\bATM operators?\b",
                          r"\bBBPOUs?\b", r"\bBharat Bill Payment\b", r"\bTReDS\b", r"\bTrade Receivables Discounting System\b",
                          r"\bNPCI\b", r"\bclearing corporations?\b"],
    "authorised_dealers": [r"\bauthori[sz]ed dealers?\b", r"\bauthori[sz]ed persons?\b", r"\bAD Category\b", r"\bAD banks?\b",
                           r"\bADs\b", r"\bmoney changers?\b", r"\bA\.\s?P\.\s?\(DIR Series\)"],
    "primary_dealers": [r"\bprimary dealers?\b", r"\bPDs\b"],
    "other": [r"\bLAF participants?\b", r"\bmarket participants?\b", r"\bmembers of the public\b", r"\bauditors?\b",
              r"\bthird[\s\-]+part(?:y|ies)\b", r"\bnon[\s\-]+bank entit(?:y|ies)\b", r"\bgovernment agencies\b",
              r"\bforeign portfolio investors?\b", r"\bFPIs?\b", r"\bnon[\s\-]+residents?\b", r"\bNRIs?\b",
              r"\bexporters?\b", r"\bimporters?\b", r"\bpersons? resident\b"],
}
# Phrases that stand for several types at once.
ALL_BANKS = re.compile(r"\ball\s+banks\b", re.I)
PAYMENT_CLASS = re.compile(r"payment system (?:providers?|operators?|participants?)|\bPSOs?\b|"
                           r"(?:authori[sz]ed|authori[sz]ation) to operate (?:a )?payment system|"
                           r"operate (?:a )?payment systems? under", re.I)
# Acronym patterns ("NBFCs", "PDs") are case-sensitive so they don't match ordinary words; the rest aren't.
_COMPILED = {t: [re.compile(p, 0 if re.search(r"\\b[A-Z]{2,}", p) else re.I) for p in ps] for t, ps in ALIASES.items()}


EXCLUSION = re.compile(r"\b(?:excluding|other than|except(?: for)?)\b[^.;)]*\)?", re.I)


def _named(text: str) -> set[str]:
    found = {t for t, ps in _COMPILED.items() if any(p.search(text) for p in ps)}
    if ALL_BANKS.search(text):
        found |= set(BANKS)
    if PAYMENT_CLASS.search(text):
        found |= set(PAYMENTS)
    return found


def named_in(text: str) -> set[str]:
    """Entity types the text names, by word or class phrase, minus any it excludes ("other than RRBs")."""
    excluded = set().union(*(_named(m.group(0)) for m in EXCLUSION.finditer(text)))
    return _named(EXCLUSION.sub(" ", text)) - excluded


def supports(text: str, entity: str) -> bool:
    """Does this quote name the entity type, directly or through a class phrase?"""
    return entity in named_in(text)
