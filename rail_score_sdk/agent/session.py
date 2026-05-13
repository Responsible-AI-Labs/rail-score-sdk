"""
Client-side agent session — accumulates tool-call results, tracks risk trends,
and detects cross-call patterns across an agent's lifecycle.

All state is held in the SDK; the engine is called atomically per tool call.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .exceptions import AgentSessionExpiredError, SessionClosedError
from .models import (
    ComplianceExposure,
    InjectionCheck,
    PlanEvaluation,
    SessionEvent,
    SessionPattern,
    SessionRiskSummary,
    ToolResultRisk,
)
from ._client import AgentDecision

# ---------------------------------------------------------------------------
# Pattern detection helpers
# ---------------------------------------------------------------------------


def _jaccard_similarity(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    """Approximate Jaccard similarity between two param dicts."""
    tokens_a = set(f"{k}={v}" for k, v in a.items())
    tokens_b = set(f"{k}={v}" for k, v in b.items())
    if not tokens_a and not tokens_b:
        return 1.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# AgentSession
# ---------------------------------------------------------------------------


class AgentSession:
    """
    Stateful session that tracks agent tool calls, accumulates risk signals,
    and detects cross-call patterns.

    Follows the same design pattern as :class:`RAILSession` for content
    evaluation but for agent tool calls.

    Args:
        client: A :class:`RailScoreClient` instance.
        agent_id: Identifier for the agent (used in summaries and events).
        compliance_frameworks: Default frameworks applied to all evaluations.
        config: Session behaviour config dict.  Supported keys:

            - ``deep_every_n`` (int, default 0): Run deep evaluation every
              N-th tool call; 0 disables.
            - ``escalate_after_flags`` (int, default 3): Switch to deep
              mode after N consecutive flags.
            - ``auto_block_after_critical`` (bool, default True): Block all
              subsequent calls after a critical compliance violation.
            - ``max_tool_calls`` (int, default 100): Auto-close after N calls.
            - ``session_ttl_minutes`` (int, default 720): Auto-close after TTL.
            - ``track_tool_results`` (bool, default True): Include tool-result
              evaluations in session tracking.

        metadata: Arbitrary key/value metadata attached to the session.
        policy_engine: Optional :class:`AgentPolicyEngine` instance.  When
            provided, policy is automatically enforced on every
            ``evaluate_tool_call`` through the session.

    Example::

        session = AgentSession(
            client,
            agent_id="lending-agent-v2",
            compliance_frameworks=["eu_ai_act"],
        )
        result = session.evaluate_tool_call(
            tool_name="credit_scoring_api",
            tool_params={"zip_code": "90210"},
            domain="finance",
        )
        print(result.decision)  # "BLOCK"
        summary = session.risk_summary()
        print(summary.risk_trend)  # "escalating"
    """

    _PATTERN_WINDOW_SECONDS = 600  # 10 minutes for repeated_pii_access

    def __init__(
        self,
        client: Any,
        agent_id: str = "agent",
        compliance_frameworks: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        policy_engine: Optional[Any] = None,
    ) -> None:
        self._c = client
        self.agent_id = agent_id
        self.compliance_frameworks = compliance_frameworks or []
        self.metadata = metadata or {}
        self._policy_engine = policy_engine

        cfg = config or {}
        self._deep_every_n: int = cfg.get("deep_every_n", 0)
        self._escalate_after_flags: int = cfg.get("escalate_after_flags", 3)
        self._auto_block_after_critical: bool = cfg.get(
            "auto_block_after_critical", True
        )
        self._max_tool_calls: int = cfg.get("max_tool_calls", 100)
        self._ttl_minutes: int = cfg.get("session_ttl_minutes", 720)
        self._track_tool_results: bool = cfg.get("track_tool_results", True)

        self.session_id: str = f"sess_{uuid.uuid4().hex[:12]}"
        self._status: str = "active"
        self._started_at: float = time.time()
        self._closed_at: Optional[float] = None

        self._history: List[SessionEvent] = []
        self._call_count: int = 0
        self._consecutive_flags: int = 0
        self._had_critical: bool = False
        self._forced_deep: bool = False

        # Counters
        self._allowed: int = 0
        self._flagged: int = 0
        self._blocked: int = 0
        self._critical_violations: int = 0
        self._total_credits: float = 0.0

        # Per-dimension score accumulator
        self._dim_scores: Dict[str, List[float]] = {}

        # Compliance exposure
        self._compliance_exposure: Dict[str, Dict[str, int]] = {}

        # Pattern state
        self._recent_tool_params: List[tuple] = []  # (tool_name, params, timestamp)
        self._pii_access_log: Dict[str, List[float]] = {}  # field -> [timestamps]
        self._detected_patterns: List[SessionPattern] = []
        self._detected_pattern_keys: set = set()

        # Track recent scores for escalating detection
        self._recent_scores: List[float] = []

    # ------------------------------------------------------------------
    # Status guards
    # ------------------------------------------------------------------

    def _assert_active(self) -> None:
        if self._status == "closed":
            raise SessionClosedError(
                f"Session {self.session_id} is closed. Create a new session."
            )
        elapsed_min = (time.time() - self._started_at) / 60.0
        if elapsed_min > self._ttl_minutes:
            self._status = "expired"
            raise AgentSessionExpiredError(
                f"Session {self.session_id} expired after {self._ttl_minutes} minutes."
            )
        if self._call_count >= self._max_tool_calls:
            self.close()
            raise SessionClosedError(
                f"Session auto-closed after {self._max_tool_calls} tool calls."
            )

    # ------------------------------------------------------------------
    # Mode selection
    # ------------------------------------------------------------------

    def _pick_mode(self, call_index: int) -> str:
        if self._forced_deep:
            return "deep"
        if self._deep_every_n > 0 and call_index % self._deep_every_n == 0:
            return "deep"
        return "basic"

    # ------------------------------------------------------------------
    # Score / pattern tracking
    # ------------------------------------------------------------------

    def _track_decision(
        self,
        event_type: str,
        tool_name: str,
        decision: str,
        rail_score: Optional[float],
        event_id: str,
        tool_params: Optional[Dict[str, Any]] = None,
        compliance_violations: Optional[List[Any]] = None,
        dimension_scores: Optional[Dict[str, Any]] = None,
        pii_entities: Optional[List[str]] = None,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        now_ts = time.time()

        self._history.append(
            SessionEvent(
                type=event_type,
                tool_name=tool_name,
                decision=decision,
                rail_score=rail_score,
                event_id=event_id,
                timestamp=now_iso,
            )
        )

        if decision == "ALLOW":
            self._allowed += 1
        elif decision == "FLAG":
            self._flagged += 1
            self._consecutive_flags += 1
        elif decision == "BLOCK":
            self._blocked += 1
            self._consecutive_flags = 0

        if decision != "FLAG":
            self._consecutive_flags = 0

        if self._consecutive_flags >= self._escalate_after_flags:
            self._forced_deep = True

        # Critical compliance check
        if compliance_violations:
            for v in compliance_violations:
                sev = getattr(
                    v, "severity", v.get("severity", "") if isinstance(v, dict) else ""
                )
                if sev == "critical":
                    self._critical_violations += 1
                    self._had_critical = True
                fw = getattr(
                    v,
                    "framework",
                    v.get("framework", "") if isinstance(v, dict) else "",
                )
                if fw:
                    if fw not in self._compliance_exposure:
                        self._compliance_exposure[fw] = {"violations": 0, "warnings": 0}
                    self._compliance_exposure[fw]["violations"] += 1

        # Dimension score accumulation
        if dimension_scores:
            for dim, ds in dimension_scores.items():
                score = getattr(
                    ds, "score", ds.get("score", 0.0) if isinstance(ds, dict) else 0.0
                )
                self._dim_scores.setdefault(dim, []).append(score)

        # Recent scores for escalating pattern
        if rail_score is not None:
            self._recent_scores.append(rail_score)
            if len(self._recent_scores) > 10:
                self._recent_scores.pop(0)

        # PII access log
        if pii_entities:
            for field in pii_entities:
                self._pii_access_log.setdefault(field, []).append(now_ts)

        # Tool params log for blocked_retry detection
        if tool_params is not None:
            self._recent_tool_params.append((tool_name, tool_params, now_ts))
            if len(self._recent_tool_params) > 20:
                self._recent_tool_params.pop(0)

        self._detect_patterns(now_ts)

    def _detect_patterns(self, now_ts: float) -> None:
        # Pattern: repeated_pii_access
        window_start = now_ts - self._PATTERN_WINDOW_SECONDS
        for field, timestamps in self._pii_access_log.items():
            recent = [t for t in timestamps if t >= window_start]
            if (
                len(recent) >= 3
                and "repeated_pii_access" not in self._detected_pattern_keys
            ):
                self._add_pattern(
                    "repeated_pii_access",
                    f"PII field '{field}' accessed {len(recent)} times in 10 minutes",
                    "high",
                )

        # Pattern: escalating_risk_scores (3 consecutive declining)
        if len(self._recent_scores) >= 3:
            last3 = self._recent_scores[-3:]
            if (
                last3[0] > last3[1] > last3[2]
                and "escalating_risk_scores" not in self._detected_pattern_keys
            ):
                self._add_pattern(
                    "escalating_risk_scores",
                    f"3 consecutive tool calls with declining RAIL scores: {last3}",
                    "medium",
                )
                self._forced_deep = True

        # Pattern: blocked_retry
        if self._blocked >= 1 and len(self._recent_tool_params) >= 2:
            last = self._recent_tool_params[-1]
            for prev in self._recent_tool_params[:-1]:
                if (
                    prev[0] == last[0]
                    and _jaccard_similarity(prev[1], last[1]) > 0.8
                    and "blocked_retry" not in self._detected_pattern_keys
                ):
                    self._add_pattern(
                        "blocked_retry",
                        f"Agent retried blocked tool '{last[0]}' with similar params "
                        f"(Jaccard > 0.8)",
                        "high",
                    )

        # Pattern: compliance_accumulation
        for fw, counts in self._compliance_exposure.items():
            key = f"compliance_accumulation_{fw}"
            if counts["violations"] >= 3 and key not in self._detected_pattern_keys:
                self._add_pattern(
                    "compliance_accumulation",
                    f"3+ compliance violations from {fw}",
                    "high",
                    key=key,
                )

        # Pattern: dimension_degradation
        for dim, scores in self._dim_scores.items():
            if len(scores) >= 3:
                last3 = scores[-3:]
                if all(s < 4.0 for s in last3):
                    key = f"dimension_degradation_{dim}"
                    if key not in self._detected_pattern_keys:
                        self._add_pattern(
                            "dimension_degradation",
                            f"Dimension '{dim}' scored < 4.0 on 3 consecutive calls",
                            "medium",
                            key=key,
                        )

    def _add_pattern(
        self,
        pattern: str,
        description: str,
        severity: str,
        key: Optional[str] = None,
    ) -> None:
        key = key or pattern
        self._detected_pattern_keys.add(key)
        self._detected_patterns.append(
            SessionPattern(
                pattern=pattern,
                description=description,
                severity=severity,
                first_seen=datetime.now(timezone.utc).isoformat(),
            )
        )

    # ------------------------------------------------------------------
    # Core evaluation methods
    # ------------------------------------------------------------------

    def evaluate_tool_call(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        domain: str = "general",
        mode: Optional[str] = None,
        compliance_frameworks: Optional[List[str]] = None,
        custom_thresholds: Optional[Dict[str, Any]] = None,
        agent_context: Optional[Dict[str, Any]] = None,
    ) -> AgentDecision:
        """Evaluate a tool call and track it in the session.

        Args:
            tool_name: Name of the tool being called.
            tool_params: Parameters that would be passed to the tool.
            domain: Content domain hint.
            mode: Override evaluation mode for this call.
            compliance_frameworks: Override compliance frameworks for this call.
            custom_thresholds: Override thresholds for this call.
            agent_context: Additional agent context.

        Returns:
            :class:`AgentDecision`.

        Raises:
            SessionClosedError: If the session is closed.
            AgentBlockedError: If a policy engine is attached and policy is
                ``BLOCK``.
        """
        self._assert_active()

        if self._had_critical and self._auto_block_after_critical:
            from .exceptions import AgentBlockedError

            raise AgentBlockedError(
                decision_reason="Session auto-blocked: prior critical compliance violation",
                rail_score=0.0,
            )

        self._call_count += 1
        effective_mode = mode or self._pick_mode(self._call_count)
        frameworks = compliance_frameworks or self.compliance_frameworks

        ctx = agent_context or {}
        ctx.setdefault("agent_id", self.agent_id)
        ctx.setdefault("session_id", self.session_id)
        ctx["session_call_index"] = self._call_count

        result = self._c.agent.evaluate_tool_call(
            tool_name=tool_name,
            tool_params=tool_params,
            agent_context=ctx,
            domain=domain,
            mode=effective_mode,
            compliance_frameworks=frameworks or None,
            custom_thresholds=custom_thresholds,
        )

        # Collect PII field names from context signals
        pii_fields = (
            result.context_signals.pii_fields_detected if result.context_signals else []
        )

        self._total_credits += result.credits_consumed
        self._track_decision(
            event_type="tool_call",
            tool_name=tool_name,
            decision=result.decision,
            rail_score=result.rail_score.score,
            event_id=result.event_id,
            tool_params=tool_params,
            compliance_violations=result.compliance_violations,
            dimension_scores=result.dimension_scores,
            pii_entities=pii_fields,
        )

        if self._policy_engine is not None:
            self._policy_engine.check(result)

        return result

    def evaluate_tool_result(
        self,
        tool_name: str,
        tool_result: Optional[str] = None,
        tool_result_data: Optional[Any] = None,
        tool_params: Optional[Dict[str, Any]] = None,
        checks: Optional[List[str]] = None,
        agent_context: Optional[Dict[str, Any]] = None,
    ) -> ToolResultRisk:
        """Evaluate a tool result and optionally track it in the session."""
        self._assert_active()

        result = self._c.agent.evaluate_tool_result(
            tool_name=tool_name,
            tool_result=tool_result,
            tool_result_data=tool_result_data,
            tool_params=tool_params,
            checks=checks,
            agent_context=agent_context,
        )

        if self._track_tool_results:
            pii_fields: List[str] = []
            if result.pii_detected and result.pii_detected.found:
                pii_fields = [e.type for e in result.pii_detected.entities]

            self._total_credits += result.credits_consumed
            self._track_decision(
                event_type="tool_result",
                tool_name=tool_name,
                decision=result.recommended_action,
                rail_score=None,
                event_id=result.event_id,
                pii_entities=pii_fields,
            )

        return result

    def check_injection(
        self,
        content: str,
        content_source: Optional[str] = None,
        agent_context: Optional[Dict[str, Any]] = None,
    ) -> InjectionCheck:
        """Check content for prompt injection and track in the session."""
        self._assert_active()

        result = self._c.agent.check_injection(
            content=content,
            content_source=content_source,
            agent_context=agent_context,
        )

        self._total_credits += result.credits_consumed
        self._track_decision(
            event_type="injection_check",
            tool_name=content_source or "unknown",
            decision="BLOCK" if result.injection_detected else "ALLOW",
            rail_score=None,
            event_id=result.event_id,
        )

        return result

    def evaluate_plan(
        self,
        plan: List[Dict[str, Any]],
        goal: str = "",
        domain: str = "general",
        mode: str = "basic",
        compliance_frameworks: Optional[List[str]] = None,
    ) -> PlanEvaluation:
        """Evaluate a multi-step plan and track all steps in the session."""
        self._assert_active()

        result = self._c.agent.evaluate_plan(
            plan=plan,
            goal=goal,
            agent_id=self.agent_id,
            domain=domain,
            mode=mode,
            compliance_frameworks=compliance_frameworks
            or self.compliance_frameworks
            or None,
        )

        self._total_credits += result.credits_consumed
        for step in result.step_results:
            self._call_count += 1
            self._track_decision(
                event_type="tool_call",
                tool_name=step.tool_name,
                decision=step.decision,
                rail_score=step.rail_score,
                event_id=f"{result.evaluated_at}_step{step.step_index}",
                compliance_violations=step.compliance_violations,
                dimension_scores=step.dimension_scores,
            )

        return result

    # ------------------------------------------------------------------
    # Summary & close
    # ------------------------------------------------------------------

    def risk_summary(self) -> SessionRiskSummary:
        """Return the current session risk summary."""
        dim_avgs = {
            dim: round(sum(scores) / len(scores), 2)
            for dim, scores in self._dim_scores.items()
            if scores
        }
        all_scores = [e.rail_score for e in self._history if e.rail_score is not None]
        current_risk = (
            round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
        )

        # Risk trend
        if len(all_scores) >= 3:
            recent3 = all_scores[-3:]
            if recent3[-1] < recent3[0] - 1.0:
                risk_trend = "escalating"
            elif recent3[-1] > recent3[0] + 1.0:
                risk_trend = "improving"
            elif current_risk < 3.0:
                risk_trend = "critical"
            else:
                risk_trend = "stable"
        elif current_risk < 3.0:
            risk_trend = "critical"
        else:
            risk_trend = "stable"

        compliance_exposure = {
            fw: ComplianceExposure(
                violations=counts["violations"],
                warnings=counts.get("warnings", 0),
            )
            for fw, counts in self._compliance_exposure.items()
        }

        duration: Optional[int] = None
        closed_at_str: Optional[str] = None
        if self._closed_at:
            duration = int(self._closed_at - self._started_at)
            closed_at_str = datetime.fromtimestamp(
                self._closed_at, tz=timezone.utc
            ).isoformat()

        return SessionRiskSummary(
            session_id=self.session_id,
            agent_id=self.agent_id,
            status=self._status,
            total_tool_calls=self._call_count,
            allowed=self._allowed,
            flagged=self._flagged,
            blocked=self._blocked,
            critical_violations=self._critical_violations,
            current_risk_score=current_risk,
            risk_trend=risk_trend,
            dimension_averages=dim_avgs,
            patterns_detected=list(self._detected_patterns),
            compliance_exposure=compliance_exposure,
            total_credits_consumed=round(self._total_credits, 4),
            duration_seconds=duration,
            closed_at=closed_at_str,
        )

    def close(self) -> SessionRiskSummary:
        """Close the session and return the final risk summary."""
        if self._status != "closed":
            self._status = "closed"
            self._closed_at = time.time()
        return self.risk_summary()

    @property
    def history(self) -> List[SessionEvent]:
        """Read-only list of all session events."""
        return list(self._history)
