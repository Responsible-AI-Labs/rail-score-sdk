"""Quick test script for Python SDK v2"""

import sys
import os

# Add the SDK to the path
sys.path.insert(0, os.path.dirname(__file__))

from rail_score_sdk import RailScoreClient


def test_client_creation():
    """Test that client can be created"""
    print("Testing Python SDK...")

    client = RailScoreClient(api_key="test-key")

    print("  Client created successfully")
    print(f"   API Key: {client.api_key[:8]}...")
    print(f"   Base URL: {client.base_url}")
    print(f"   Timeout: {client.timeout}s")

    # Verify auth header format changed to Bearer
    assert "Bearer test-key" in client.session.headers.get("Authorization", "")
    print("   Auth header: Bearer token")

    return client


def test_imports():
    """Test that all v2 components can be imported"""
    print("\nTesting imports...")

    from rail_score_sdk import (
        # Client
        RailScoreClient,
        # Eval models
        RailScore,
        DimensionScore,
        Issue,
        EvalResult,
        # Protected models
        ProtectedEvalResult,
        ProtectedRegenerateResult,
        RegenerateMetadata,
        # Compliance models
        ComplianceScore,
        ComplianceDimensionScore,
        RequirementResult,
        ComplianceIssue,
        RiskClassificationDetail,
        ComplianceResult,
        CrossFrameworkSummary,
        MultiComplianceResult,
        # Utility models
        HealthResponse,
        VersionResponse,
        # Exceptions
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

    print("  All imports successful")

    components = [
        "RailScoreClient",
        "RailScore",
        "DimensionScore",
        "Issue",
        "EvalResult",
        "ProtectedEvalResult",
        "ProtectedRegenerateResult",
        "ComplianceResult",
        "MultiComplianceResult",
        "HealthResponse",
        "VersionResponse",
        "RailScoreError",
        "AuthenticationError",
        "InsufficientCreditsError",
        "ValidationError",
        "ContentTooHarmfulError",
        "RateLimitError",
    ]

    for component in components:
        print(f"   - {component}")


def test_methods_exist():
    """Test that all v2 methods exist on the client"""
    print("\nTesting methods...")

    client = RailScoreClient(api_key="test-key")

    methods = [
        "eval",
        "protected_evaluate",
        "protected_regenerate",
        "compliance_check",
        "health",
        "version",
    ]

    for method in methods:
        assert hasattr(client, method), f"Method {method} not found"
        print(f"   {method}()")

    print("  All methods exist")


def test_version():
    """Test version is 2.0.0"""
    print("\nTesting version...")

    from rail_score_sdk import __version__

    assert __version__ == "2.0.0", f"Expected 2.0.0, got {__version__}"
    print(f"  Version: {__version__}")


def test_class_constants():
    """Test that client class constants are correct"""
    print("\nTesting class constants...")

    assert "fairness" in RailScoreClient.VALID_DIMENSIONS
    assert "user_impact" in RailScoreClient.VALID_DIMENSIONS
    assert len(RailScoreClient.VALID_DIMENSIONS) == 8
    print(f"  VALID_DIMENSIONS: {len(RailScoreClient.VALID_DIMENSIONS)} dimensions")

    assert "basic" in RailScoreClient.VALID_MODES
    assert "deep" in RailScoreClient.VALID_MODES
    print(f"  VALID_MODES: {RailScoreClient.VALID_MODES}")

    assert "gdpr" in RailScoreClient.VALID_FRAMEWORKS
    assert "eu_ai_act" in RailScoreClient.VALID_FRAMEWORKS
    assert "india_dpdp" in RailScoreClient.VALID_FRAMEWORKS
    assert len(RailScoreClient.VALID_FRAMEWORKS) == 6
    print(f"  VALID_FRAMEWORKS: {len(RailScoreClient.VALID_FRAMEWORKS)} frameworks")

    # Test aliases
    assert RailScoreClient.FRAMEWORK_ALIASES["dpdp"] == "india_dpdp"
    assert RailScoreClient.FRAMEWORK_ALIASES["ai_act"] == "eu_ai_act"
    print(f"  FRAMEWORK_ALIASES: {len(RailScoreClient.FRAMEWORK_ALIASES)} aliases")


if __name__ == "__main__":
    print("=" * 60)
    print("RAIL Score Python SDK v2 - Quick Test")
    print("=" * 60)

    try:
        test_imports()
        test_client_creation()
        test_methods_exist()
        test_version()
        test_class_constants()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPython SDK v2 is ready to use!")

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
