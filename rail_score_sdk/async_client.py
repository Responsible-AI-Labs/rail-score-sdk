"""
Async wrapper around the RAIL Score HTTP API.

Usage:
    from rail_score_sdk.async_client import AsyncRAILClient

    async with AsyncRAILClient(api_key="rail_xxx") as client:
        result = await client.eval("Some AI-generated text", mode="basic")
        print(result["rail_score"]["score"])
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional

import httpx


_DEFAULT_BASE_URL = "https://api.responsibleailabs.ai"
_CACHE_TTL_SECONDS = 300  # 5 minutes


class AsyncRAILClient:
    """Non-blocking HTTP client for the RAIL Score API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 2,
        enable_cache: bool = True,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self._cache: Dict[str, tuple[float, Any]] = {}
        self._client: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "AsyncRAILClient":
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _cache_key(self, endpoint: str, payload: Dict[str, Any]) -> str:
        raw = f"{endpoint}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[Any]:
        if not self.enable_cache or key not in self._cache:
            return None
        ts, data = self._cache[key]
        if time.time() - ts > _CACHE_TTL_SECONDS:
            del self._cache[key]
            return None
        return data

    def _set_cached(self, key: str, data: Any) -> None:
        if self.enable_cache:
            self._cache[key] = (time.time(), data)

    async def _request(
        self, method: str, path: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self._client is None:
            raise RuntimeError(
                "Client not initialised. Use `async with AsyncRAILClient(...) as c:`"
            )

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                if method == "POST":
                    resp = await self._client.post(path, json=payload)
                else:
                    resp = await self._client.get(path)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (429, 500, 502, 503):
                    last_exc = exc
                    await asyncio.sleep(min(2**attempt, 8))
                    continue
                raise
            except httpx.RequestError as exc:
                last_exc = exc
                await asyncio.sleep(min(2**attempt, 8))
        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Public API wrappers
    # ------------------------------------------------------------------
    async def eval(
        self,
        content: str,
        *,
        mode: str = "basic",
        dimensions: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
        context: str = "",
        domain: str = "general",
        usecase: str = "general",
        include_explanations: Optional[bool] = None,
        include_issues: Optional[bool] = None,
        include_suggestions: bool = False,
    ) -> Dict[str, Any]:
        """POST /railscore/v1/eval"""
        payload: Dict[str, Any] = {
            "content": content,
            "mode": mode,
            "domain": domain,
            "usecase": usecase,
            "include_suggestions": include_suggestions,
        }
        if dimensions:
            payload["dimensions"] = dimensions
        if weights:
            payload["weights"] = weights
        if context:
            payload["context"] = context
        if include_explanations is not None:
            payload["include_explanations"] = include_explanations
        if include_issues is not None:
            payload["include_issues"] = include_issues

        cache_key = self._cache_key("/railscore/v1/eval", payload)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        data = await self._request("POST", "/railscore/v1/eval", payload)
        result = data.get("result", data)
        self._set_cached(cache_key, result)
        return result

    async def safe_regenerate(
        self,
        content: str,
        *,
        mode: str = "basic",
        max_regenerations: int = 3,
        regeneration_model: str = "RAIL_Safe_LLM",
        thresholds: Optional[Dict[str, Any]] = None,
        context: str = "",
        domain: str = "general",
        usecase: str = "general",
        user_query: str = "",
        weights: Optional[Dict[str, float]] = None,
        policy_hint: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """POST /railscore/v1/safe-regenerate"""
        payload: Dict[str, Any] = {
            "content": content,
            "mode": mode,
            "max_regenerations": max_regenerations,
            "regeneration_model": regeneration_model,
            "domain": domain,
            "usecase": usecase,
        }
        if thresholds:
            payload["thresholds"] = thresholds
        if context:
            payload["context"] = context
        if user_query:
            payload["user_query"] = user_query
        if weights:
            payload["weights"] = weights
        if policy_hint:
            payload["policy_hint"] = policy_hint

        data = await self._request("POST", "/railscore/v1/safe-regenerate", payload)
        return data

    async def safe_regenerate_continue(
        self,
        session_id: str,
        regenerated_content: str,
    ) -> Dict[str, Any]:
        """POST /railscore/v1/safe-regenerate/continue"""
        payload = {
            "session_id": session_id,
            "regenerated_content": regenerated_content,
        }
        data = await self._request(
            "POST", "/railscore/v1/safe-regenerate/continue", payload
        )
        return data

    async def compliance_check(
        self,
        content: str,
        *,
        framework: Optional[str] = None,
        frameworks: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        strict_mode: bool = False,
    ) -> Dict[str, Any]:
        """POST /railscore/v1/compliance/check"""
        payload: Dict[str, Any] = {"content": content, "strict_mode": strict_mode}
        if framework:
            payload["framework"] = framework
        if frameworks:
            payload["frameworks"] = frameworks
        if context:
            payload["context"] = context

        data = await self._request("POST", "/railscore/v1/compliance/check", payload)
        return data.get("result", data.get("results", data))

    async def health(self) -> Dict[str, str]:
        """GET /health"""
        return await self._request("GET", "/health")
