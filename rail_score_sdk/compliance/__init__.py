"""
India DPDP behavioral compliance module for RAIL Score SDK.

Provides content scanning, event-driven compliance, and audit capabilities
aligned with the Digital Personal Data Protection Act 2023 and DPDP Rules 2025.
"""

from .dpdp import (
    DPDPConfig,
    DPDPContentScanner,
    DPDPContentResult,
    DPDPViolation,
    DPDPPiiMatch,
    DPDPChildSignal,
)

__all__ = [
    "DPDPConfig",
    "DPDPContentScanner",
    "DPDPContentResult",
    "DPDPViolation",
    "DPDPPiiMatch",
    "DPDPChildSignal",
]
