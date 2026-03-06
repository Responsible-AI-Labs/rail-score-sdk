"""RAIL Score API client implementation."""

import requests
from typing import Optional, Dict, Any, List, Union
from .models import (
    RailScore,
    DimensionScore,
    Issue,
    EvalResult,
    SafeRegenerateResult,
    SafeRegenerateMetadata,
    CreditsBreakdown,
    IterationRecord,
    RailPrompt,
    CriticalContentEvaluation,
    ComplianceScore,
    ComplianceDimensionScore,
    RequirementResult,
    ComplianceIssue,
    RiskClassificationDetail,
    ComplianceResult,
    CrossFrameworkSummary,
    MultiComplianceResult,
    HealthResponse,
)
from .exceptions import (
    RailScoreError,
    AuthenticationError,
    InsufficientCreditsError,
    InsufficientTierError,
    ValidationError,
    ContentTooHarmfulError,
    SessionExpiredError,
    RateLimitError,
    EvaluationFailedError,
    NotImplementedByServerError,
    ServiceUnavailableError,
)


class RailScoreClient:
    """
    Official RAIL Score Python SDK.

    Provides methods to interact with all RAIL Score API endpoints
    for evaluating AI-generated content across 8 dimensions of
    Responsible AI.

    Args:
        api_key: Your RAIL Score API key.
        base_url: API base URL (default: https://api.responsibleailabs.ai).
        timeout: Request timeout in seconds (default: 30).

    Example:
        >>> client = RailScoreClient(api_key="rail_xxx...")
        >>> result = client.eval(
        ...     content="AI should prioritize human welfare.",
        ...     mode="basic",
        ... )
        >>> print(f"Score: {result.rail_score.score}/10")
    """

    VALID_DIMENSIONS = frozenset(
        [
            "fairness",
            "safety",
            "reliability",
            "transparency",
            "privacy",
            "accountability",
            "inclusivity",
            "user_impact",
        ]
    )

    VALID_MODES = frozenset(["basic", "deep"])

    VALID_DOMAINS = frozenset(
        ["general", "healthcare", "finance", "legal", "education", "code"]
    )

    VALID_USECASES = frozenset(
        [
            "general",
            "chatbot",
            "content_generation",
            "summarization",
            "translation",
            "code_generation",
        ]
    )

    VALID_FRAMEWORKS = frozenset(
        ["gdpr", "ccpa", "hipaa", "eu_ai_act", "india_dpdp", "india_ai_gov"]
    )

    FRAMEWORK_ALIASES = {
        "ai_act": "eu_ai_act",
        "euaia": "eu_ai_act",
        "dpdp": "india_dpdp",
        "ai_governance": "india_ai_gov",
        "india_ai": "india_ai_gov",
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.responsibleailabs.ai",
        timeout: int = 30,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        authenticated: bool = True,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method.
            endpoint: API endpoint path.
            json: JSON request body.
            params: Query parameters.
            authenticated: Whether to include the auth header (default True).

        Returns:
            Parsed JSON response dict.

        Raises:
            RailScoreError: On API or network errors.
        """
        url = f"{self.base_url}{endpoint}"

        headers = {}
        if not authenticated:
            headers["Authorization"] = ""

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                timeout=self.timeout,
                headers=headers if not authenticated else None,
            )

            if not response.ok:
                self._handle_error(response)

            return response.json()

        except requests.exceptions.Timeout:
            raise RailScoreError("Request timeout", status_code=None)
        except requests.exceptions.RequestException as e:
            raise RailScoreError(f"Network error: {str(e)}", status_code=None)

    def _handle_error(self, response: requests.Response) -> None:
        """Map HTTP status codes to typed exceptions."""
        try:
            error_data = response.json()
            error_message = error_data.get("error", "Unknown error")
        except Exception:
            error_data = {}
            error_message = response.text or "Unknown error"

        status = response.status_code
        if status == 400:
            raise ValidationError(error_message, status, error_data)
        elif status == 401:
            raise AuthenticationError(error_message, status, error_data)
        elif status == 402:
            raise InsufficientCreditsError(error_message, status, error_data)
        elif status == 403:
            raise InsufficientTierError(error_message, status, error_data)
        elif status == 410:
            raise SessionExpiredError(error_message, status, error_data)
        elif status == 422:
            raise ContentTooHarmfulError(error_message, status, error_data)
        elif status == 429:
            raise RateLimitError(error_message, status, error_data)
        elif status == 500:
            raise EvaluationFailedError(error_message, status, error_data)
        elif status == 501:
            raise NotImplementedByServerError(error_message, status, error_data)
        elif status == 503:
            raise ServiceUnavailableError(error_message, status, error_data)
        else:
            raise RailScoreError(error_message, status, error_data)

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_rail_score(data: Dict[str, Any]) -> RailScore:
        return RailScore(
            score=data["score"],
            confidence=data["confidence"],
            summary=data["summary"],
        )

    @staticmethod
    def _parse_dimension_scores(
        data: Dict[str, Any],
    ) -> Dict[str, DimensionScore]:
        scores = {}
        for dim, info in data.items():
            scores[dim] = DimensionScore(
                score=info["score"],
                confidence=info["confidence"],
                explanation=info.get("explanation"),
                issues=info.get("issues"),
            )
        return scores

    @staticmethod
    def _parse_issues(data: Optional[List[Dict[str, Any]]]) -> Optional[List[Issue]]:
        if data is None:
            return None
        return [Issue(dimension=i["dimension"], description=i["description"]) for i in data]

    @staticmethod
    def _parse_requirement(data: Dict[str, Any]) -> RequirementResult:
        return RequirementResult(
            requirement_id=data["requirement_id"],
            requirement=data["requirement"],
            article=data["article"],
            reference_url=data["reference_url"],
            status=data["status"],
            score=data["score"],
            confidence=data["confidence"],
            threshold=data["threshold"],
            ai_specific=data["ai_specific"],
            dimension_sources=data["dimension_sources"],
            evaluation_method=data["evaluation_method"],
            issue=data.get("issue"),
            regulatory_deadline=data.get("regulatory_deadline"),
            penalty_exposure=data.get("penalty_exposure"),
        )

    @staticmethod
    def _parse_compliance_issue(data: Dict[str, Any]) -> ComplianceIssue:
        return ComplianceIssue(
            id=data["id"],
            description=data["description"],
            dimension=data["dimension"],
            severity=data["severity"],
            requirement=data["requirement"],
            article=data["article"],
            reference_url=data["reference_url"],
            remediation_effort=data["remediation_effort"],
            remediation_deadline_days=data.get("remediation_deadline_days"),
            remediation_deadline_date=data.get("remediation_deadline_date"),
        )

    def _parse_compliance_result(self, data: Dict[str, Any]) -> ComplianceResult:
        dim_scores = {}
        for dim, info in data.get("dimension_scores", {}).items():
            dim_scores[dim] = ComplianceDimensionScore(
                score=info["score"],
                confidence=info["confidence"],
                explanation=info.get("explanation"),
                issues=info.get("issues"),
            )

        risk_detail = None
        if data.get("risk_classification_detail"):
            rd = data["risk_classification_detail"]
            risk_detail = RiskClassificationDetail(
                tier=rd["tier"],
                basis=rd["basis"],
                obligations=rd.get("obligations"),
            )

        return ComplianceResult(
            framework=data["framework"],
            framework_version=data["framework_version"],
            framework_url=data["framework_url"],
            evaluated_at=data["evaluated_at"],
            compliance_score=ComplianceScore(
                score=data["compliance_score"]["score"],
                confidence=data["compliance_score"]["confidence"],
                label=data["compliance_score"]["label"],
                summary=data["compliance_score"]["summary"],
            ),
            dimension_scores=dim_scores,
            requirements_checked=data["requirements_checked"],
            requirements_passed=data["requirements_passed"],
            requirements_failed=data["requirements_failed"],
            requirements_warned=data["requirements_warned"],
            requirements=[self._parse_requirement(r) for r in data.get("requirements", [])],
            issues=[self._parse_compliance_issue(i) for i in data.get("issues", [])],
            improvement_suggestions=data.get("improvement_suggestions", []),
            risk_classification_detail=risk_detail,
            partial_result=data.get("partial_result", False),
            from_cache=data.get("from_cache", False),
            credits=data.get("_credits"),
        )

    @staticmethod
    def _parse_iteration_record(data: Dict[str, Any]) -> IterationRecord:
        return IterationRecord(
            iteration=data["iteration"],
            content=data.get("content", ""),
            scores=data.get("scores"),
            thresholds_met=data.get("thresholds_met"),
            failing_dimensions=data.get("failing_dimensions"),
            improvement_from_previous=data.get("improvement_from_previous"),
            latency_ms=data.get("latency_ms"),
            rail_prompt=data.get("rail_prompt"),
            regeneration_model=data.get("regeneration_model"),
        )

    def _parse_safe_regenerate(self, data: Dict[str, Any]) -> SafeRegenerateResult:
        result = data["result"]

        metadata = None
        if "metadata" in data:
            m = data["metadata"]
            metadata = SafeRegenerateMetadata(
                req_id=m.get("req_id", ""),
                mode=m.get("mode", ""),
                total_iterations=m.get("total_iterations"),
                total_latency_ms=m.get("total_latency_ms"),
            )

        credits_breakdown = None
        if "credits_breakdown" in data:
            cb = data["credits_breakdown"]
            credits_breakdown = CreditsBreakdown(
                evaluations=cb["evaluations"],
                regenerations=cb["regenerations"],
                total=cb["total"],
            )

        rail_prompt = None
        if result.get("rail_prompt") and isinstance(result["rail_prompt"], dict):
            rp = result["rail_prompt"]
            rail_prompt = RailPrompt(
                system_prompt=rp.get("system_prompt", ""),
                user_prompt=rp.get("user_prompt", ""),
                temperature=rp.get("temperature"),
            )

        iteration_history = None
        if result.get("iteration_history"):
            iteration_history = [
                self._parse_iteration_record(rec)
                for rec in result["iteration_history"]
            ]

        return SafeRegenerateResult(
            status=result["status"],
            original_content=result.get("original_content", ""),
            credits_consumed=data.get("credits_consumed", 0.0),
            metadata=metadata,
            credits_breakdown=credits_breakdown,
            best_content=result.get("best_content"),
            best_iteration=result.get("best_iteration"),
            best_scores=result.get("best_scores"),
            iteration_history=iteration_history,
            session_id=result.get("session_id"),
            iteration=result.get("iteration"),
            iterations_remaining=result.get("iterations_remaining"),
            current_scores=result.get("current_scores"),
            rail_prompt=rail_prompt,
        )

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def eval(
        self,
        content: str,
        mode: str = "basic",
        dimensions: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
        context: Optional[str] = None,
        domain: str = "general",
        usecase: str = "general",
        include_explanations: Optional[bool] = None,
        include_issues: Optional[bool] = None,
        include_suggestions: bool = False,
    ) -> EvalResult:
        """Evaluate content across RAIL dimensions.

        Supports two modes:
        - **basic**: Fast, cost-efficient scoring.
        - **deep**: Detailed scoring with per-dimension explanations.

        Args:
            content: Text to evaluate (10 -- 10,000 characters).
            mode: ``"basic"`` or ``"deep"``.
            dimensions: Subset of dimensions to evaluate.  Valid values:
                ``fairness``, ``safety``, ``reliability``, ``transparency``,
                ``privacy``, ``accountability``, ``inclusivity``, ``user_impact``.
                Defaults to all 8.
            weights: Custom weights per dimension.  **Must sum to 100.**
            context: Additional evaluation context
                (e.g. ``"This is a medical chatbot response"``).
            domain: ``general``, ``healthcare``, ``finance``, ``legal``,
                ``education``, or ``code``.
            usecase: ``general``, ``chatbot``, ``content_generation``,
                ``summarization``, ``translation``, or ``code_generation``.
            include_explanations: Include per-dimension text explanations.
                Defaults to ``False`` for basic, ``True`` for deep.
            include_issues: Include per-dimension issue lists.
                Defaults to ``False`` for basic, ``True`` for deep.
            include_suggestions: Include improvement suggestions for
                low-scoring dimensions.

        Returns:
            :class:`EvalResult` with scores and optional explanations.

        Raises:
            ValidationError: Invalid parameters.
            AuthenticationError: Missing or invalid credentials.
            InsufficientCreditsError: Not enough credits.

        Example:
            >>> result = client.eval(
            ...     content="Exercise improves cardiovascular health.",
            ...     mode="basic",
            ... )
            >>> print(result.rail_score.summary)
        """
        payload: Dict[str, Any] = {
            "content": content,
            "mode": mode,
            "domain": domain,
            "usecase": usecase,
            "include_suggestions": include_suggestions,
        }
        if dimensions is not None:
            payload["dimensions"] = dimensions
        if weights is not None:
            payload["weights"] = weights
        if context is not None:
            payload["context"] = context
        if include_explanations is not None:
            payload["include_explanations"] = include_explanations
        if include_issues is not None:
            payload["include_issues"] = include_issues

        data = self._request("POST", "/railscore/v1/eval", json=payload)
        result = data["result"]

        return EvalResult(
            rail_score=self._parse_rail_score(result["rail_score"]),
            explanation=result.get("explanation", ""),
            dimension_scores=self._parse_dimension_scores(result["dimension_scores"]),
            issues=self._parse_issues(result.get("issues")),
            improvement_suggestions=result.get("improvement_suggestions"),
            from_cache=result.get("from_cache", False),
        )

    # ------------------------------------------------------------------
    # Safe-Regenerate
    # ------------------------------------------------------------------

    def safe_regenerate(
        self,
        content: str,
        mode: str = "basic",
        max_regenerations: int = 3,
        regeneration_model: str = "RAIL_Safe_LLM",
        thresholds: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
        domain: str = "general",
        usecase: str = "general",
        user_query: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
        policy_hint: Optional[Dict[str, str]] = None,
    ) -> SafeRegenerateResult:
        """Evaluate content and iteratively regenerate until RAIL thresholds are met.

        Two regeneration models:

        - ``"RAIL_Safe_LLM"`` (default): Server handles everything in a
          single call and returns the final result.
        - ``"external"``: Client-orchestrated mode.  Returns evaluation +
          prompt; call :meth:`safe_regenerate_continue` with your own
          regenerated content.

        Args:
            content: Content to evaluate/regenerate (10 -- 10,000 characters).
            mode: ``"basic"`` or ``"deep"``.
            max_regenerations: Maximum regeneration attempts (1 -- 5).
            regeneration_model: ``"RAIL_Safe_LLM"`` or ``"external"``.
            thresholds: Threshold configuration.  Example::

                {
                    "overall": {"score": 8.0, "confidence": 0.5},
                    "tradeoff_mode": "priority",
                    "max_dimension_failures": 2,
                    "dimensions": {"safety": 8.0},
                }

            context: Additional context for evaluation.
            domain: Content domain hint.
            usecase: Use case hint.
            user_query: Original user query for context.
            weights: Dimension weights (must sum to 100).
            policy_hint: Policy hint, e.g. ``{"on_failure": "return_best"}``.

        Returns:
            :class:`SafeRegenerateResult`.  Check ``result.status``:

            - ``"passed"``: Content met all thresholds.
            - ``"max_iterations_reached"``: Hit max without passing.
            - ``"awaiting_regeneration"``: External mode -- use
              ``result.rail_prompt`` and ``result.session_id`` with
              :meth:`safe_regenerate_continue`.

        Raises:
            ContentTooHarmfulError: Content scored below 3.0 (422).
            ValidationError: Invalid parameters.
            AuthenticationError: Missing or invalid credentials.
            InsufficientCreditsError: Not enough credits.

        Example:
            >>> result = client.safe_regenerate(
            ...     content="Our AI collects user data. We use it for stuff.",
            ...     thresholds={"overall": {"score": 8.0}},
            ...     max_regenerations=2,
            ... )
            >>> if result.status == "passed":
            ...     print(result.best_content)
        """
        payload: Dict[str, Any] = {
            "content": content,
            "mode": mode,
            "max_regenerations": max_regenerations,
            "regeneration_model": regeneration_model,
            "domain": domain,
            "usecase": usecase,
        }
        if thresholds is not None:
            payload["thresholds"] = thresholds
        if context is not None:
            payload["context"] = context
        if user_query is not None:
            payload["user_query"] = user_query
        if weights is not None:
            payload["weights"] = weights
        if policy_hint is not None:
            payload["policy_hint"] = policy_hint

        data = self._request("POST", "/railscore/v1/safe-regenerate", json=payload)
        return self._parse_safe_regenerate(data)

    def safe_regenerate_continue(
        self,
        session_id: str,
        regenerated_content: str,
    ) -> SafeRegenerateResult:
        """Continue an external-mode safe-regenerate session.

        After receiving an ``"awaiting_regeneration"`` response from
        :meth:`safe_regenerate` with ``regeneration_model="external"``,
        regenerate the content yourself and submit it here.

        Args:
            session_id: Session ID from the initial response (starts with ``sr_``).
            regenerated_content: Your regenerated content (10 -- 10,000 characters).

        Returns:
            :class:`SafeRegenerateResult`.  Possible statuses:

            - ``"passed"``: Thresholds met.
            - ``"awaiting_regeneration"``: Still needs improvement.
            - ``"max_iterations_reached"``: No more iterations.

        Raises:
            SessionExpiredError: Session expired (410).  Sessions last 15 minutes.
            ValidationError: Invalid parameters.

        Example:
            >>> # Step 1: Start external session
            >>> result = client.safe_regenerate(
            ...     content="...", regeneration_model="external"
            ... )
            >>> # Step 2: Regenerate content yourself using result.rail_prompt
            >>> improved = my_llm_call(result.rail_prompt.user_prompt)
            >>> # Step 3: Continue
            >>> result = client.safe_regenerate_continue(
            ...     session_id=result.session_id,
            ...     regenerated_content=improved,
            ... )
        """
        payload: Dict[str, Any] = {
            "session_id": session_id,
            "regenerated_content": regenerated_content,
        }

        data = self._request(
            "POST", "/railscore/v1/safe-regenerate/continue", json=payload
        )
        return self._parse_safe_regenerate(data)

    # ------------------------------------------------------------------
    # Compliance
    # ------------------------------------------------------------------

    def compliance_check(
        self,
        content: str,
        framework: Optional[str] = None,
        frameworks: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False,
        include_explanations: bool = True,
    ) -> Union[ComplianceResult, MultiComplianceResult]:
        """Evaluate content against regulatory compliance frameworks.

        Provide either ``framework`` (single) or ``frameworks`` (list of
        up to 5).

        Supported frameworks: ``gdpr``, ``ccpa``, ``hipaa``, ``eu_ai_act``,
        ``india_dpdp``, ``india_ai_gov``.

        Args:
            content: Content to evaluate (max 50,000 characters).
            framework: Single framework ID.
            frameworks: List of framework IDs (max 5).
            context: Evaluation context with optional keys:
                ``domain``, ``system_type``, ``jurisdiction``,
                ``data_subjects``, ``decision_type``,
                ``processes_personal_data``, ``high_risk_indicators``.
            strict_mode: Use stricter threshold evaluation.
            include_explanations: Include per-dimension explanations.

        Returns:
            :class:`ComplianceResult` for single framework, or
            :class:`MultiComplianceResult` for multiple frameworks.

        Raises:
            ValidationError: Invalid or missing framework.
            InsufficientTierError: Plan tier too low for the framework.
            RateLimitError: Daily compliance check limit reached.
            AuthenticationError: Missing or invalid credentials.

        Example:
            >>> result = client.compliance_check(
            ...     content="Our AI processes browsing history...",
            ...     framework="gdpr",
            ...     context={"domain": "e-commerce"},
            ... )
            >>> print(result.compliance_score.summary)
        """
        if framework is None and frameworks is None:
            raise ValueError("Either 'framework' or 'frameworks' must be provided.")
        if framework is not None and frameworks is not None:
            raise ValueError("Provide 'framework' or 'frameworks', not both.")

        payload: Dict[str, Any] = {
            "content": content,
            "strict_mode": strict_mode,
            "include_explanations": include_explanations,
        }
        if framework is not None:
            resolved = self.FRAMEWORK_ALIASES.get(framework, framework)
            payload["framework"] = resolved
        if frameworks is not None:
            payload["frameworks"] = [
                self.FRAMEWORK_ALIASES.get(f, f) for f in frameworks
            ]
        if context is not None:
            payload["context"] = context

        data = self._request("POST", "/railscore/v1/compliance/check", json=payload)

        # Multi-framework response
        if "results" in data:
            parsed_results = {}
            for fw_key, fw_data in data["results"].items():
                parsed_results[fw_key] = self._parse_compliance_result(fw_data)

            summary_data = data["cross_framework_summary"]
            summary = CrossFrameworkSummary(
                frameworks_evaluated=summary_data["frameworks_evaluated"],
                average_score=summary_data["average_score"],
                weakest_framework=summary_data["weakest_framework"],
                weakest_score=summary_data["weakest_score"],
                credits=summary_data.get("_credits"),
            )
            return MultiComplianceResult(
                results=parsed_results,
                cross_framework_summary=summary,
            )

        # Single-framework response
        return self._parse_compliance_result(data["result"])

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def health(self) -> HealthResponse:
        """Check API health status.  No authentication required.

        Returns:
            :class:`HealthResponse`.

        Example:
            >>> h = client.health()
            >>> print(h.status)
        """
        data = self._request("GET", "/health", authenticated=False)
        return HealthResponse(status=data["status"], service=data["service"])
