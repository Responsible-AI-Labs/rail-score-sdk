"""DPDP-specific exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .models import DPDPRequiredAction, DPDPTimer, DPDPViolation


class DPDPError(Exception):
    """Base exception for DPDP compliance errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.details = details or {}
        super().__init__(message)


class DPDPBlockedError(DPDPError):
    """Raised when content is blocked due to a DPDP violation."""

    def __init__(
        self,
        message: str,
        violations: Optional[List["DPDPViolation"]] = None,
        check: str = "",
        section: str = "",
    ) -> None:
        self.violations = violations or []
        self.check = check
        self.section = section
        super().__init__(message)


class DPDPChildContentBlockedError(DPDPBlockedError):
    """Raised when child-targeted content is blocked (S.9(3))."""
    pass


class DPDPPiiBlockedError(DPDPBlockedError):
    """Raised when PII is detected with ``pii_action='block'`` (S.8(5))."""
    pass


class DPDPConsentRequiredError(DPDPError):
    """Raised when evaluate() returns 'require_action' due to missing consent."""

    def __init__(
        self,
        message: str,
        required_actions: Optional[List["DPDPRequiredAction"]] = None,
        missing_consent_purpose: str = "",
    ) -> None:
        self.required_actions = required_actions or []
        self.missing_consent_purpose = missing_consent_purpose
        super().__init__(message)


class DPDPTimerExpiredError(DPDPError):
    """Raised when a compliance timer deadline has passed."""

    def __init__(
        self,
        message: str,
        timer: Optional["DPDPTimer"] = None,
    ) -> None:
        self.timer = timer
        super().__init__(message)


class DPDPSessionNotFoundError(DPDPError):
    """Raised when a session ID is not found or has expired."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"DPDP session not found: {session_id}")
