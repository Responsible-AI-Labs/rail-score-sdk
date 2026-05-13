"""Client-side DPDP content scanner — zero-latency PII and child signal detection."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, List, Optional, Tuple

from .constants import (
    CHILD_AGE_PATTERNS,
    CHILD_AGE_THRESHOLD,
    CHILD_CONTEXT_PATTERNS,
    CHILD_MINOR_KEYWORDS,
    CHILD_PARENTAL_PATTERNS,
    CHILD_SCHOOL_PATTERNS,
    PII_MASKERS,
    PII_PATTERNS,
    SECTION_REFS,
    verhoeff_validate,
)
from .models import (
    DPDPChildSignal,
    DPDPContentResult,
    DPDPPiiMatch,
    DPDPViolation,
)

if TYPE_CHECKING:
    from .config import DPDPConfig


class DPDPContentScanner:
    """Client-side regex scanner for Indian PII and child signals.

    Runs entirely locally with zero network latency.  For richer
    server-side analysis (Verhoeff checksums on full corpus, bank handle
    validation, semantic purpose-drift), use ``client.dpdp.scan()``.
    """

    def __init__(self, config: DPDPConfig) -> None:
        self._config = config
        self._active_patterns = {
            k: v for k, v in PII_PATTERNS.items()
            if k in config.pii_patterns
        }

    def scan_text(
        self,
        text: str,
        session_flags: Optional[List[str]] = None,
    ) -> DPDPContentResult:
        """Run all DPDP pattern checks on *text*.

        Parameters
        ----------
        text : str
            The text to scan.
        session_flags : list[str], optional
            Existing session flags (e.g. ``["child_data_detected"]``).

        Returns
        -------
        DPDPContentResult
        """
        flags = list(session_flags or [])
        pii_found = self._detect_pii(text)
        child_signals = self._detect_child_signals(text)
        violations: List[DPDPViolation] = []

        if child_signals:
            flags = list(set(flags) | {"child_data_detected"})

        child_targeting = self._check_child_targeting(text, flags)
        if child_targeting:
            violations.append(child_targeting)

        purpose_violation = self._check_purpose_drift(text)
        if purpose_violation:
            violations.append(purpose_violation)

        if pii_found:
            violations.append(DPDPViolation(
                check="pii_leak",
                section=SECTION_REFS["pii_leak"],
                reason=f"Indian PII detected: {', '.join(sorted({p.type for p in pii_found}))}",
                action=self._config.pii_action,
                found=", ".join(p.type for p in pii_found),
                severity="critical",
            ))

        compliant = len(violations) == 0
        return DPDPContentResult(
            compliant=compliant,
            violations=violations,
            pii_found=pii_found,
            child_signals=child_signals,
            session_flags=flags,
            original_content=text,
        )

    def apply_actions(
        self,
        result: DPDPContentResult,
        text: str,
    ) -> Tuple[str, DPDPContentResult]:
        """Apply configured actions (mask/block/warn) and return processed text.

        Returns
        -------
        tuple[str, DPDPContentResult]
            The (possibly masked) text and the updated result.
        """
        processed = text

        if result.pii_found and self._config.pii_action == "mask":
            processed = self._mask_pii(processed, result.pii_found)
            result.masked_content = processed

        if result.pii_found and self._config.pii_action == "block":
            processed = self._block_text(
                "[Content blocked: Indian PII detected in output]"
            )
            result.masked_content = processed

        if "child_data_detected" in result.session_flags:
            for v in result.violations:
                if v.check == "child_targeting" and self._config.child_content_action == "block":
                    processed = self._block_text(
                        "[Content blocked: behavioral targeting not permitted for users under 18]"
                    )
                    result.masked_content = processed
                    break

        return processed, result

    # ------------------------------------------------------------------
    # PII detection
    # ------------------------------------------------------------------

    def _detect_pii(self, text: str) -> List[DPDPPiiMatch]:
        matches: List[DPDPPiiMatch] = []
        for pii_type, pattern in self._active_patterns.items():
            for m in pattern.finditer(text):
                raw = m.group()

                if pii_type == "aadhaar":
                    digits = raw.replace(" ", "")
                    if not verhoeff_validate(digits):
                        continue

                masker = PII_MASKERS.get(pii_type)
                masked = masker(m) if masker else f"[{pii_type.upper()}]"

                matches.append(DPDPPiiMatch(
                    type=pii_type,
                    value=raw,
                    start=m.start(),
                    end=m.end(),
                    masked_value=masked,
                ))
        return matches

    def _mask_pii(self, text: str, pii_matches: List[DPDPPiiMatch]) -> str:
        sorted_matches = sorted(pii_matches, key=lambda m: m.start, reverse=True)
        result = text
        for pm in sorted_matches:
            result = result[:pm.start] + pm.masked_value + result[pm.end:]
        return result

    @staticmethod
    def _block_text(message: str) -> str:
        return message

    # ------------------------------------------------------------------
    # Child signal detection
    # ------------------------------------------------------------------

    def _detect_child_signals(self, text: str) -> List[DPDPChildSignal]:
        signals: List[DPDPChildSignal] = []

        for pattern in CHILD_AGE_PATTERNS:
            for m in pattern.finditer(text):
                age = int(m.group(1))
                if age < CHILD_AGE_THRESHOLD:
                    signals.append(DPDPChildSignal(
                        signal_type="age_mention",
                        evidence=m.group().strip(),
                        detected_age=age,
                    ))

        for pattern in CHILD_CONTEXT_PATTERNS:
            for m in pattern.finditer(text):
                age = int(m.group(1))
                if age < CHILD_AGE_THRESHOLD:
                    signals.append(DPDPChildSignal(
                        signal_type="age_mention",
                        evidence=m.group().strip(),
                        detected_age=age,
                    ))

        for pattern in CHILD_SCHOOL_PATTERNS:
            for m in pattern.finditer(text):
                grade_str = m.group(1)
                inferred_age = None
                try:
                    grade_num = int(grade_str)
                    inferred_age = grade_num + 5
                    if inferred_age >= CHILD_AGE_THRESHOLD:
                        continue
                except ValueError:
                    pass
                signals.append(DPDPChildSignal(
                    signal_type="grade_mention",
                    evidence=m.group().strip(),
                    detected_age=inferred_age,
                ))

        if CHILD_MINOR_KEYWORDS.search(text):
            m = CHILD_MINOR_KEYWORDS.search(text)
            signals.append(DPDPChildSignal(
                signal_type="minor_keyword",
                evidence=m.group().strip(),
            ))

        if CHILD_PARENTAL_PATTERNS.search(text):
            m = CHILD_PARENTAL_PATTERNS.search(text)
            signals.append(DPDPChildSignal(
                signal_type="parental_reference",
                evidence=m.group().strip(),
            ))

        return signals

    # ------------------------------------------------------------------
    # Child targeting check
    # ------------------------------------------------------------------

    def _check_child_targeting(
        self,
        text: str,
        session_flags: List[str],
    ) -> Optional[DPDPViolation]:
        if "child_data_detected" not in session_flags:
            return None

        targeting_patterns = [
            r'\bbased\s+on\s+(?:his|her|their|your)\s+(?:browsing|behavior|activity|profile|purchase)',
            r'\brecommend(?:ed|ation|s)?\b.*\b(?:product|supplement|purchase|buy)\b',
            r'\btargeted\s+(?:ad|advertisement|content|offer)',
            r'\bsimilar\s+users?\s+(?:also\s+)?(?:bought|purchased|liked)',
            r'\bpersonali[sz]ed\s+(?:offer|deal|recommendation)',
            r'\bbehavioral\s+(?:tracking|monitoring|profiling|analysis)',
        ]

        for pat_str in targeting_patterns:
            if re.search(pat_str, text, re.IGNORECASE):
                return DPDPViolation(
                    check="child_targeting",
                    section=SECTION_REFS["child_targeting"],
                    reason="Behavioral recommendation for minor-flagged session",
                    action=self._config.child_content_action,
                    severity="critical",
                )
        return None

    # ------------------------------------------------------------------
    # Purpose drift check
    # ------------------------------------------------------------------

    def _check_purpose_drift(self, text: str) -> Optional[DPDPViolation]:
        if not self._config.purpose:
            return None

        drift_indicators = {
            "advertising": ["advertis", "promo", "sponsored", "retarget", "campaign"],
            "tracking": ["track", "monitor", "surveillance", "fingerprint"],
            "profiling": ["profil", "behavioral analysis", "predict"],
            "selling_data": ["sell data", "share with third part", "data broker"],
        }

        purpose_lower = self._config.purpose.lower()
        text_lower = text.lower()

        for drift_type, keywords in drift_indicators.items():
            if drift_type in purpose_lower:
                continue
            for kw in keywords:
                if kw in text_lower:
                    return DPDPViolation(
                        check="purpose_drift",
                        section=SECTION_REFS["purpose_drift"],
                        reason=(
                            f"Output contains '{kw}' which may drift from "
                            f"declared purpose '{self._config.purpose}'"
                        ),
                        action=self._config.purpose_drift_action,
                        severity="medium",
                    )
        return None
