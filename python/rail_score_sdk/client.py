"""RAIL Score API client implementation."""

import requests
from typing import Optional, Dict, Any, List, Union
from .models import (
    RailScore,
    DimensionScore,
    Issue,
    EvalResult,
    ProtectedEvalResult,
    ProtectedRegenerateResult,
    RegenerateMetadata,
    ComplianceScore,
    ComplianceDimensionScore,
    RequirementResult,
    ComplianceIssue,
    RiskClassificationDetail,
    ComplianceResult,
    CrossFrameworkSummary,
    MultiComplianceResult,
    HealthResponse,
    VersionResponse,
)
from .exceptions import (
    RailScoreError,
    AuthenticationError,
    InsufficientCreditsError,
    InsufficientTierError,
    ValidationError,
    ContentTooHarmfulError,
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
        api_key: Your RAIL Score API key or JWT token.
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
        - **basic**: Hybrid ML scoring (fast, cheaper).
        - **deep**: LLM-as-Judge with per-dimension explanations.

        Args:
            content: Text to evaluate (10 – 10,000 characters).
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
    # Protected content
    # ------------------------------------------------------------------

    def protected_evaluate(
        self,
        content: str,
        threshold: float = 7.0,
        mode: str = "basic",
        user_query: Optional[str] = None,
        llm_prompt: Optional[str] = None,
        domain: str = "general",
        usecase: str = "general",
    ) -> ProtectedEvalResult:
        """Evaluate content against a quality threshold.

        If the content scores below the threshold, an improvement prompt
        is returned that can be used to regenerate better content.

        Args:
            content: AI-generated content (10 – 10,000 characters).
            threshold: Minimum acceptable RAIL score (0.0 – 10.0).
            mode: ``"basic"`` or ``"deep"``.
            user_query: Original user query for context.
            llm_prompt: Original LLM prompt used to generate the content.
            domain: Content domain.
            usecase: Use case category.

        Returns:
            :class:`ProtectedEvalResult` with threshold status and optional
            improvement prompt.

        Raises:
            ValidationError: Invalid parameters.
            AuthenticationError: Missing or invalid credentials.

        Example:
            >>> result = client.protected_evaluate(
            ...     content="You should never trust anyone over 40.",
            ...     threshold=7.0,
            ... )
            >>> if result.improvement_needed:
            ...     print(result.improvement_prompt)
        """
        payload: Dict[str, Any] = {
            "content": content,
            "action": "evaluate",
            "threshold": threshold,
            "mode": mode,
            "domain": domain,
            "usecase": usecase,
        }
        if user_query is not None:
            payload["user_query"] = user_query
        if llm_prompt is not None:
            payload["llm_prompt"] = llm_prompt

        data = self._request("POST", "/railscore/v1/protected", json=payload)
        result = data["result"]

        dim_scores = None
        if "dimension_scores" in result:
            dim_scores = self._parse_dimension_scores(result["dimension_scores"])

        return ProtectedEvalResult(
            rail_score=self._parse_rail_score(result["rail_score"]),
            threshold_met=result["threshold_met"],
            improvement_needed=result["improvement_needed"],
            improvement_prompt=result.get("improvement_prompt"),
            dimension_scores=dim_scores,
        )

    def protected_regenerate(
        self,
        content: str,
        issues_to_fix: Optional[Dict[str, Any]] = None,
        domain: str = "general",
        usecase: str = "general",
    ) -> ProtectedRegenerateResult:
        """Regenerate improved content using the RAIL engine.

        Args:
            content: Content to regenerate (10 – 10,000 characters).
            issues_to_fix: Dict of ``dimension → {score, explanation, issues}``
                describing what to fix.
            domain: Content domain.
            usecase: Use case category.

        Returns:
            :class:`ProtectedRegenerateResult` with the improved content.

        Raises:
            ContentTooHarmfulError: Average issue score below 3.0.
            ValidationError: Invalid parameters.
            AuthenticationError: Missing or invalid credentials.

        Example:
            >>> result = client.protected_regenerate(
            ...     content="You should never trust anyone over 40.",
            ...     issues_to_fix={
            ...         "fairness": {
            ...             "score": 2.0,
            ...             "explanation": "Age-based stereotyping.",
            ...             "issues": ["Age-based stereotyping"],
            ...         }
            ...     },
            ... )
            >>> print(result.improved_content)
        """
        payload: Dict[str, Any] = {
            "content": content,
            "action": "regenerate",
            "domain": domain,
            "usecase": usecase,
        }
        if issues_to_fix is not None:
            payload["issues_to_fix"] = issues_to_fix

        data = self._request("POST", "/railscore/v1/protected", json=payload)
        result = data["result"]

        meta = None
        if "metadata" in result:
            m = result["metadata"]
            meta = RegenerateMetadata(
                model=m["model"],
                input_tokens=m["input_tokens"],
                output_tokens=m["output_tokens"],
                total_tokens=m.get("total_tokens"),
            )

        return ProtectedRegenerateResult(
            improved_content=result["improved_content"],
            issues_addressed=result["issues_addressed"],
            metadata=meta,
        )

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
                ``domain``, ``system_type``, ``data_types``,
                ``processing_purpose``, ``risk_indicators``, ``cross_border``.
            strict_mode: Use 8.5 pass threshold instead of 7.0.
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

    def version(self) -> VersionResponse:
        """Get API version information.  No authentication required.

        Returns:
            :class:`VersionResponse`.

        Example:
            >>> v = client.version()
            >>> print(v.version)
        """
        data = self._request("GET", "/version", authenticated=False)
        return VersionResponse(
            version=data["version"],
            api_version=data["api_version"],
            optimizations=data.get("optimizations", {}),
            models_available=data.get("models_available", []),
        )

