"""Custom exceptions for the RAIL Score SDK."""


class RailScoreError(Exception):
    """Base exception for all RAIL Score SDK errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class AuthenticationError(RailScoreError):
    """Raised when authentication fails (401).

    Missing or invalid Authorization: Bearer header.
    """

    pass


class InsufficientCreditsError(RailScoreError):
    """Raised when account has insufficient credits (402).

    Attributes:
        balance: Current credit balance.
        required: Credits required for the request.
    """

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message, status_code, response)
        self.balance = response.get("balance") if response else None
        self.required = response.get("required") if response else None


class InsufficientTierError(RailScoreError):
    """Raised when feature requires a higher plan tier (403)."""

    pass


class ValidationError(RailScoreError):
    """Raised when request validation fails (400).

    Examples: invalid mode, invalid framework, content too short/long,
    weights don't sum to 100, invalid dimension names.
    """

    pass


class ContentTooHarmfulError(RailScoreError):
    """Raised when content is critically unsafe (422).

    The safe-regenerate endpoint refuses to regenerate content with an
    average score below 3.0.  The ``response`` dict contains the
    evaluation details and ``credits_consumed``.
    """

    pass


class SessionExpiredError(RailScoreError):
    """Raised when a safe-regenerate session has expired (410).

    External-mode sessions expire after 15 minutes.
    """

    pass


class RateLimitError(RailScoreError):
    """Raised when rate limit is exceeded (429)."""

    pass


class EvaluationFailedError(RailScoreError):
    """Raised on internal evaluation errors (500). Retry is safe."""

    pass


class NotImplementedByServerError(RailScoreError):
    """Raised when a feature is not yet implemented (501)."""

    pass


class ServiceUnavailableError(RailScoreError):
    """Raised when service is temporarily unavailable (503)."""

    pass
