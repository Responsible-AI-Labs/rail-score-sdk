"""DPDPConfig — configuration dataclass for India DPDP compliance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, List, Optional

from .constants import (
    VALID_CHILD_ACTIONS,
    VALID_DRIFT_ACTIONS,
    VALID_ENTITY_TYPES,
    VALID_PII_ACTIONS,
    VALID_SECTORS,
)


@dataclass
class DPDPConfig:
    """Configuration for India DPDP behavioral compliance.

    Controls how the SDK detects, masks, and blocks DPDP-relevant
    patterns in AI-generated content and how it interacts with the
    DPDP compliance API endpoints.

    Parameters
    ----------
    entity_type : str
        ``"data_fiduciary"`` or ``"significant_data_fiduciary"``.
    sector : str
        Industry sector: ``fintech``, ``healthcare``, ``edtech``,
        ``e_commerce``, ``social_media``, or ``other``.
    purpose : str
        Declared processing purpose for purpose-limitation checks.
    pii_action : str
        Action on detected PII: ``detect``, ``mask``, ``block``,
        ``warn``, or ``log``.
    child_content_action : str
        Action on child-targeted content: ``block``, ``warn``, or ``log``.
    purpose_drift_action : str
        Action when output drifts from declared purpose: ``block``,
        ``warn``, or ``log``.
    processes_children : bool
        Enable Section 9 child-data monitoring.
    cross_border_transfers : bool
        Enable Section 16 cross-border transfer checks.
    indian_users : int
        Approximate number of Indian users (Third Schedule threshold).
    pii_patterns : list[str]
        Which PII types to detect. Defaults to Aadhaar, PAN, mobile, UPI.
    dsr_sla_days : int
        DSR response deadline in days (Rule 14(3) default: 90).
    pre_erasure_notice_hours : int
        Hours before erasure to notify user (Rule 8 default: 48).
    breach_dpbi_hours : int
        DPBI detailed report deadline (Rule 7 default: 72).
    breach_certin_hours : int
        CERT-In incident report deadline (default: 6).
    on_violation : callable, optional
        Async callback invoked on each violation.
    on_timer_due : callable, optional
        Async callback invoked when a compliance timer fires.
    """

    entity_type: str = "data_fiduciary"
    sector: str = "other"
    purpose: str = ""

    pii_action: str = "mask"
    child_content_action: str = "block"
    purpose_drift_action: str = "warn"

    processes_children: bool = False
    cross_border_transfers: bool = False
    indian_users: int = 0

    pii_patterns: List[str] = field(
        default_factory=lambda: ["aadhaar", "pan", "mobile_in", "upi"]
    )

    dsr_sla_days: int = 90
    pre_erasure_notice_hours: int = 48
    breach_dpbi_hours: int = 72
    breach_certin_hours: int = 6

    on_violation: Optional[Callable[..., Awaitable[None]]] = None
    on_timer_due: Optional[Callable[..., Awaitable[None]]] = None

    def __post_init__(self) -> None:
        if self.entity_type not in VALID_ENTITY_TYPES:
            raise ValueError(
                f"entity_type must be one of {sorted(VALID_ENTITY_TYPES)}, "
                f"got {self.entity_type!r}"
            )
        if self.sector not in VALID_SECTORS:
            raise ValueError(
                f"sector must be one of {sorted(VALID_SECTORS)}, "
                f"got {self.sector!r}"
            )
        if self.pii_action not in VALID_PII_ACTIONS:
            raise ValueError(
                f"pii_action must be one of {sorted(VALID_PII_ACTIONS)}, "
                f"got {self.pii_action!r}"
            )
        if self.child_content_action not in VALID_CHILD_ACTIONS:
            raise ValueError(
                f"child_content_action must be one of {sorted(VALID_CHILD_ACTIONS)}, "
                f"got {self.child_content_action!r}"
            )
        if self.purpose_drift_action not in VALID_DRIFT_ACTIONS:
            raise ValueError(
                f"purpose_drift_action must be one of {sorted(VALID_DRIFT_ACTIONS)}, "
                f"got {self.purpose_drift_action!r}"
            )

    def to_scan_config(self) -> dict:
        """Convert to the ``config`` dict expected by the ``/scan`` endpoint."""
        cfg: dict = {
            "pii_action": self.pii_action if self.pii_action != "mask" else "mask",
            "child_detection": self.processes_children or True,
        }
        if self.purpose:
            cfg["purpose"] = self.purpose
        return cfg

    def to_session_config(self) -> dict:
        """Convert to the ``config`` dict expected by the ``/session`` endpoint."""
        cfg: dict = {
            "entity_type": self.entity_type,
            "purpose": self.purpose,
            "sector": self.sector,
            "processes_children": self.processes_children,
        }
        return cfg
