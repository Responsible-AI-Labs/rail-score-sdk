"""
Error handling example for RAIL Score Python SDK.

This example demonstrates how to properly handle different types of errors
that may occur when using the RAIL Score API.
"""

from rail_score_sdk import (
    RailScoreClient,
    RailScoreError,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError,
)
import time

# Initialize the client
client = RailScoreClient(
    api_key='your-rail-api-key-here'
)

print("=" * 70)
print("RAIL Score SDK - Error Handling Examples")
print("=" * 70)

# Example 1: Authentication Error
print("\nExample 1: Handling Authentication Errors")
print("-" * 70)

try:
    # This will fail with invalid API key
    invalid_client = RailScoreClient(api_key='invalid_key_12345')
    result = invalid_client.calculate(
        content="Test content",
        domain='general'
    )
except AuthenticationError as e:
    print(f"❌ Authentication failed: {e.message}")
    print(f"   Status Code: {e.status_code}")
    print(f"   Solution: Check your API key at https://responsibleailabs.ai/dashboard")
except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")

# Example 2: Validation Error
print("\n\nExample 2: Handling Validation Errors")
print("-" * 70)

try:
    # This will fail due to invalid domain
    result = client.calculate(
        content="Test content",
        domain='invalid_domain'  # Invalid domain
    )
except ValidationError as e:
    print(f"❌ Validation error: {e.message}")
    print(f"   Status Code: {e.status_code}")
    if e.response:
        print(f"   Details: {e.response}")
    print(f"   Solution: Use valid domain: general, healthcare, law, hr, politics, news, finance")
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Example 3: Insufficient Credits Error
print("\n\nExample 3: Handling Insufficient Credits")
print("-" * 70)

try:
    # This might fail if you're out of credits
    result = client.calculate(
        content="AI ethics in healthcare" * 100,  # Large content
        domain='healthcare'
    )
    print(f"✓ Success! RAIL Score: {result.rail_score}/10")
except InsufficientCreditsError as e:
    print(f"❌ Insufficient credits: {e.message}")
    print(f"   Status Code: {e.status_code}")
    print(f"   Solutions:")
    print(f"   1. Purchase credit topup at https://responsibleailabs.ai/pricing")
    print(f"   2. Upgrade to higher plan (Pro/Business/Enterprise)")
    print(f"   3. Wait for monthly credit renewal (Free/Pro plans)")
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Example 4: Rate Limit Error
print("\n\nExample 4: Handling Rate Limits")
print("-" * 70)

def make_requests_with_retry(max_retries=3, retry_delay=2):
    """Make API request with exponential backoff on rate limit."""
    for attempt in range(max_retries):
        try:
            result = client.calculate(
                content="Testing rate limits with RAIL Score API",
                domain='general',
                explain_scores=False  # Faster
            )
            print(f"✓ Request succeeded on attempt {attempt + 1}")
            print(f"  RAIL Score: {result.rail_score}/10")
            return result

        except RateLimitError as e:
            print(f"⚠ Rate limit exceeded (attempt {attempt + 1}/{max_retries})")
            print(f"  Message: {e.message}")

            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                print(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"  Max retries reached. Please try again later.")
                return None

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return None

make_requests_with_retry()

# Example 5: Generic API Error
print("\n\nExample 5: Handling Generic API Errors")
print("-" * 70)

try:
    # Any other API errors
    result = client.calculate(
        content="Content for evaluation",
        domain='general'
    )
    print(f"✓ Success! RAIL Score: {result.rail_score}/10")
except RailScoreError as e:
    # Catches any RAIL Score API error
    print(f"❌ API Error: {e.message}")
    print(f"   Status Code: {e.status_code}")
    if e.response:
        print(f"   Response: {e.response}")
except Exception as e:
    # Catches network errors, timeouts, etc.
    print(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")

# Example 6: Comprehensive Error Handling
print("\n\nExample 6: Comprehensive Error Handling Pattern")
print("-" * 70)

def evaluate_content_safely(content, domain='general'):
    """
    Safely evaluate content with comprehensive error handling.

    Returns:
        dict: {'success': bool, 'data': result or None, 'error': str or None}
    """
    try:
        result = client.calculate(
            content=content,
            domain=domain,
            explain_scores=True
        )

        return {
            'success': True,
            'data': result,
            'error': None
        }

    except AuthenticationError as e:
        return {
            'success': False,
            'data': None,
            'error': f'Authentication failed: {e.message}. Check your API key.'
        }

    except ValidationError as e:
        return {
            'success': False,
            'data': None,
            'error': f'Invalid request: {e.message}. Please check your input.'
        }

    except InsufficientCreditsError as e:
        return {
            'success': False,
            'data': None,
            'error': f'Insufficient credits: {e.message}. Purchase more credits or upgrade plan.'
        }

    except RateLimitError as e:
        return {
            'success': False,
            'data': None,
            'error': f'Rate limit exceeded: {e.message}. Please wait before retrying.'
        }

    except RailScoreError as e:
        return {
            'success': False,
            'data': None,
            'error': f'API error: {e.message} (Status: {e.status_code})'
        }

    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': f'Unexpected error: {type(e).__name__}: {str(e)}'
        }

# Test the comprehensive error handler
response = evaluate_content_safely(
    content="AI systems should prioritize transparency and user privacy.",
    domain='general'
)

if response['success']:
    result = response['data']
    print(f"✓ Evaluation successful!")
    print(f"  RAIL Score: {result.rail_score}/10")
    print(f"  Grade: {result.grade}")
else:
    print(f"❌ Evaluation failed!")
    print(f"  Error: {response['error']}")

# Example 7: Timeout Handling
print("\n\nExample 7: Handling Timeouts")
print("-" * 70)

try:
    # Create client with short timeout for demonstration
    timeout_client = RailScoreClient(
        api_key='your-rail-api-key-here',
        timeout=1  # 1 second timeout (very short)
    )

    result = timeout_client.calculate(
        content="This might timeout with a very short timeout setting.",
        domain='general'
    )
    print(f"✓ Request completed: {result.rail_score}/10")

except RailScoreError as e:
    if 'timeout' in str(e.message).lower():
        print(f"⏱ Request timeout: {e.message}")
        print(f"   Solution: Increase timeout value when creating client")
        print(f"   Example: RailScoreClient(api_key='...', timeout=60)")
    else:
        print(f"❌ Error: {e.message}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Best Practices Summary
print("\n" + "=" * 70)
print("Best Practices for Error Handling")
print("=" * 70)
print("""
1. Always wrap API calls in try-except blocks
2. Handle specific exceptions before generic ones
3. Implement retry logic for rate limits (exponential backoff)
4. Log errors for debugging and monitoring
5. Provide user-friendly error messages
6. Set appropriate timeout values based on your use case
7. Validate input before making API calls
8. Check credit balance before bulk operations
9. Handle network errors (connection issues, timeouts)
10. Use the comprehensive error handling pattern for production code
""")

print("=" * 70)
print("Error Handling Examples Complete!")
print("=" * 70)
