"""DPDP compliance constants: PII patterns, child signals, section references."""

import re

# ---------------------------------------------------------------------------
# Indian PII regex patterns
# ---------------------------------------------------------------------------

AADHAAR_PATTERN = re.compile(r"\b([2-9]\d{3})\s?(\d{4})\s?(\d{4})\b")

PAN_PATTERN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")

MOBILE_IN_PATTERN = re.compile(r"\b(?:\+91[\s\-]?|0)?[6-9]\d{9}\b")

UPI_PATTERN = re.compile(
    r"\b[\w.\-]+@(?:ybl|paytm|oksbi|okaxis|okicici|okhdfcbank|upi|apl|"
    r"ibl|axl|sbi|icici|hdfcbank|kotak|indus|rbl|federal|idbi|citi|"
    r"barodampay|unionbankofindia|cnrb|pnb|bob|mahabank|dbs|"
    r"jupiteraxis|freecharge|phonepe|gpay|slice|niyox)\b",
    re.IGNORECASE,
)

VOTER_ID_PATTERN = re.compile(r"\b[A-Z]{3}\d{7}\b")

PASSPORT_PATTERN = re.compile(r"\b[JKLMRSTUVZ]\d{7}\b")

DRIVING_LICENSE_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}\s?\d{4}\s?\d{7}\b")

IFSC_PATTERN = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")

BANK_ACCOUNT_CONTEXT_PATTERN = re.compile(
    r"(?:account|a/c|acct|bank\s*a/c)[\s#:.\-]*(\d{9,18})\b",
    re.IGNORECASE,
)

GSTIN_PATTERN = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9]\b")

PII_PATTERNS = {
    "aadhaar": AADHAAR_PATTERN,
    "pan": PAN_PATTERN,
    "mobile_in": MOBILE_IN_PATTERN,
    "upi": UPI_PATTERN,
    "voter_id": VOTER_ID_PATTERN,
    "passport": PASSPORT_PATTERN,
    "driving_license": DRIVING_LICENSE_PATTERN,
    "ifsc": IFSC_PATTERN,
    "bank_account": BANK_ACCOUNT_CONTEXT_PATTERN,
    "gstin": GSTIN_PATTERN,
}

# Verhoeff checksum tables for Aadhaar validation
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_validate(number_str: str) -> bool:
    """Validate a number string using the Verhoeff checksum algorithm."""
    digits = [int(d) for d in number_str if d.isdigit()]
    c = 0
    for i, digit in enumerate(reversed(digits)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][digit]]
    return c == 0


# ---------------------------------------------------------------------------
# PII masking functions
# ---------------------------------------------------------------------------


def mask_aadhaar(match: re.Match) -> str:
    """Mask Aadhaar: show last 4 digits only."""
    raw = match.group().replace(" ", "")
    return f"XXXX XXXX {raw[-4:]}"


def mask_pan(match: re.Match) -> str:
    """Mask PAN: show digits and last letter, mask first 5 letters."""
    val = match.group()
    return f"XXXXX{val[5:]}"


def mask_mobile(match: re.Match) -> str:
    return "[MOBILE]"


def mask_upi(match: re.Match) -> str:
    handle = match.group().split("@")[-1]
    return f"XXXX@{handle}"


def mask_generic(pii_type: str):
    """Return a generic masking function for a given PII type."""
    label = pii_type.upper()

    def _mask(match: re.Match) -> str:
        return f"[{label}]"

    return _mask


PII_MASKERS = {
    "aadhaar": mask_aadhaar,
    "pan": mask_pan,
    "mobile_in": mask_mobile,
    "upi": mask_upi,
    "voter_id": mask_generic("VOTER_ID"),
    "passport": mask_generic("PASSPORT"),
    "driving_license": mask_generic("DL"),
    "ifsc": mask_generic("IFSC"),
    "bank_account": mask_generic("BANK_ACCOUNT"),
    "gstin": mask_generic("GSTIN"),
}

# ---------------------------------------------------------------------------
# Child signal patterns
# ---------------------------------------------------------------------------

CHILD_AGE_PATTERNS = [
    re.compile(
        r"\b(?:I\s+am|I\'m|i\s+am|i\'m|my\s+age\s+is|age[d]?)\s+"
        r"(?:under\s+)?(\d{1,2})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(\d{1,2})\s*(?:year|yr)s?\s*old\b",
        re.IGNORECASE,
    ),
]

CHILD_CONTEXT_PATTERNS = [
    re.compile(
        r"\bmy\s+(?:son|daughter|child|kid|boy|girl)\s+(?:is\s+)?"
        r"(?:aged?\s+)?(\d{1,2})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bmy\s+(?:son|daughter|child|kid|boy|girl)\b.*?\b(\d{1,2})\s*"
        r"(?:year|yr)s?\s*old\b",
        re.IGNORECASE,
    ),
]

CHILD_SCHOOL_PATTERNS = [
    re.compile(
        r"\b(?:class|grade|standard)\s*(\d{1,2}|[IVX]+)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:\d{1,2}th|[IVX]+th)\s+(?:class|grade|standard)\b", re.IGNORECASE),
]

CHILD_MINOR_KEYWORDS = re.compile(
    r"\b(?:I\s+am\s+a\s+minor|i\s+am\s+underage|i\'m\s+a\s+minor)\b",
    re.IGNORECASE,
)

CHILD_PARENTAL_PATTERNS = re.compile(
    r"\b(?:my\s+(?:parents?|mom|dad|mother|father|guardian)\s+"
    r"(?:said|told|asked|wants?))\b",
    re.IGNORECASE,
)

# Age threshold for DPDP Act Section 9
CHILD_AGE_THRESHOLD = 18

# ---------------------------------------------------------------------------
# DPDP Section references
# ---------------------------------------------------------------------------

SECTION_REFS = {
    "pii_leak": "S.8(5)",
    "child_data": "S.9",
    "child_targeting": "S.9(3)",
    "child_tracking": "S.9(3)(b)",
    "child_advertising": "S.9(3)(c)",
    "consent_missing": "S.6",
    "notice_missing": "S.5",
    "purpose_drift": "S.6",
    "purpose_limitation": "S.4",
    "data_minimisation": "S.4",
    "security_safeguards": "S.8(5)",
    "breach_notification": "S.8(6)",
    "retention_erasure": "S.8(7)",
    "rights_grievance": "S.11-14",
    "processor_governance": "S.8(1)-(2)",
    "cross_border": "S.16",
    "accuracy_decisions": "S.8(3)",
}

# ---------------------------------------------------------------------------
# Event type taxonomy (for Phase 2)
# ---------------------------------------------------------------------------

CONSENT_EVENTS = frozenset(
    [
        "notice.shown",
        "consent.granted",
        "consent.refused",
        "consent.withdrawn",
    ]
)

DECISION_EVENTS = frozenset(
    [
        "decision.made",
        "explanation.shown",
        "appeal.opened",
        "appeal.resolved",
    ]
)

DSR_EVENTS = frozenset(
    [
        "dsr.received",
        "dsr.acknowledged",
        "dsr.responded",
        "dsr.escalated",
    ]
)

DATA_LIFECYCLE_EVENTS = frozenset(
    [
        "data.collected",
        "data.shared",
        "data.transferred",
        "retention.started",
        "erasure.executed",
        "breach.detected",
    ]
)

CHILD_EVENTS = frozenset(
    [
        "child.detected",
        "child.parental_consent",
        "child.tracking_attempted",
        "child.aged_out",
    ]
)

MODEL_EVENTS = frozenset(
    [
        "model.deployed",
        "model.retrained",
    ]
)

AGGREGATE_EVENTS = frozenset(
    [
        "aggregate.fairness_metrics",
        "aggregate.decision_stats",
    ]
)

ALL_EVENT_TYPES = (
    CONSENT_EVENTS
    | DECISION_EVENTS
    | DSR_EVENTS
    | DATA_LIFECYCLE_EVENTS
    | CHILD_EVENTS
    | MODEL_EVENTS
    | AGGREGATE_EVENTS
)

# ---------------------------------------------------------------------------
# Valid configuration values
# ---------------------------------------------------------------------------

VALID_ENTITY_TYPES = frozenset(["data_fiduciary", "significant_data_fiduciary"])
VALID_SECTORS = frozenset(
    [
        "fintech",
        "finance",
        "banking",
        "healthcare",
        "edtech",
        "e_commerce",
        "social_media",
        "other",
    ]
)
VALID_PII_ACTIONS = frozenset(["detect", "mask", "block", "warn", "log"])
VALID_CHILD_ACTIONS = frozenset(["block", "warn", "log"])
VALID_DRIFT_ACTIONS = frozenset(["block", "warn", "log"])

VALID_EVALUATE_ACTIONS = frozenset(
    [
        "process_data",
        "make_decision",
        "share_data",
        "transfer_cross_border",
        "serve_ad",
        "track_user",
    ]
)

VALID_WORKFLOW_STEPS = frozenset(
    [
        "data_collection",
        "data_processing",
        "decision_making",
        "decision_communication",
        "data_retention",
        "dsr_handling",
    ]
)

VALID_EVIDENCE_TYPES = frozenset(
    [
        "dsr_response",
        "breach_notification_dpbi",
        "breach_notification_principal",
        "breach_notification_certin",
        "compliance_health",
        "consent_audit",
        "child_protection_audit",
        "sdf_annual_report",
    ]
)
