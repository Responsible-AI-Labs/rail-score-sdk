"""
Batch processing example for RAIL Score Python SDK.

This example demonstrates how to efficiently process multiple pieces of
content using the RAIL Score API, including error handling and progress tracking.
"""

from rail_score_sdk import RailScoreClient
from rail_score_sdk import (
    RailScoreError,
    RateLimitError,
    AuthenticationError,
    ValidationError
)
import time
from typing import List, Dict, Any

# Initialize the client
client = RailScoreClient(
    api_key='your-rail-api-key-here'
)

# Sample content for batch processing
content_samples = [
    {
        "id": "article_1",
        "domain": "healthcare",
        "content": "AI is transforming healthcare by enabling early disease detection and personalized treatment plans."
    },
    {
        "id": "article_2",
        "domain": "finance",
        "content": "Machine learning algorithms can detect fraudulent transactions with high accuracy while protecting customer privacy."
    },
    {
        "id": "article_3",
        "domain": "law",
        "content": "Legal AI systems must be transparent and explainable to ensure fair and unbiased judicial recommendations."
    },
    {
        "id": "article_4",
        "domain": "hr",
        "content": "AI-powered hiring tools should be regularly audited for bias to ensure equal opportunity for all candidates."
    },
    {
        "id": "article_5",
        "domain": "news",
        "content": "Responsible journalism requires fact-checking and source verification, especially when covering AI-generated content."
    },
]

# Example 1: Basic Batch Processing
print("=" * 60)
print("Example 1: Basic Batch Processing")
print("=" * 60)

results = []

for i, item in enumerate(content_samples, 1):
    print(f"\nProcessing {i}/{len(content_samples)}: {item['id']}")

    try:
        result = client.calculate(
            content=item['content'],
            domain=item['domain'],
            explain_scores=True
        )

        results.append({
            'id': item['id'],
            'rail_score': result.rail_score,
            'grade': result.grade,
            'domain': item['domain'],
            'success': True
        })

        print(f"  ✓ Score: {result.rail_score}/10 ({result.grade})")

    except Exception as e:
        results.append({
            'id': item['id'],
            'error': str(e),
            'success': False
        })
        print(f"  ✗ Error: {str(e)}")

print(f"\n\nProcessed: {len(results)} items")
print(f"Success: {sum(1 for r in results if r['success'])}")
print(f"Failed: {sum(1 for r in results if not r['success'])}")

# Example 2: Batch Processing with Error Handling and Retry
print("\n" + "=" * 60)
print("Example 2: Batch Processing with Error Handling")
print("=" * 60)

def process_batch_with_retry(
    items: List[Dict[str, Any]],
    max_retries: int = 3,
    retry_delay: int = 2
) -> List[Dict[str, Any]]:
    """Process batch with retry logic for failed items."""
    results = []

    for i, item in enumerate(items, 1):
        print(f"\nProcessing {i}/{len(items)}: {item['id']}")

        for attempt in range(max_retries):
            try:
                result = client.calculate(
                    content=item['content'],
                    domain=item['domain'],
                    explain_scores=True
                )

                results.append({
                    'id': item['id'],
                    'rail_score': result.rail_score,
                    'grade': result.grade,
                    'dimension_scores': {
                        dim: details.score
                        for dim, details in result.dimension_scores.items()
                    },
                    'success': True,
                    'attempts': attempt + 1
                })

                print(f"  ✓ Score: {result.rail_score}/10 (Attempt {attempt + 1})")
                break

            except RateLimitError:
                print(f"  ⚠ Rate limit exceeded (Attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"  ⏳ Waiting {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    results.append({
                        'id': item['id'],
                        'error': 'Rate limit exceeded',
                        'success': False
                    })

            except ValidationError as e:
                print(f"  ✗ Validation error: {e.message}")
                results.append({
                    'id': item['id'],
                    'error': f'Validation error: {e.message}',
                    'success': False
                })
                break

            except AuthenticationError:
                print(f"  ✗ Authentication failed")
                results.append({
                    'id': item['id'],
                    'error': 'Authentication failed',
                    'success': False
                })
                break

            except RailScoreError as e:
                print(f"  ✗ API error: {e.message}")
                if attempt < max_retries - 1:
                    print(f"  ⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    results.append({
                        'id': item['id'],
                        'error': str(e),
                        'success': False
                    })

    return results

results_with_retry = process_batch_with_retry(content_samples[:3])

print(f"\n\nBatch Processing Summary:")
print(f"Total: {len(results_with_retry)}")
print(f"Success: {sum(1 for r in results_with_retry if r['success'])}")
print(f"Failed: {sum(1 for r in results_with_retry if not r['success'])}")

# Example 3: Aggregate Statistics
print("\n" + "=" * 60)
print("Example 3: Aggregate Statistics from Batch Results")
print("=" * 60)

successful_results = [r for r in results if r.get('success', False)]

if successful_results:
    avg_score = sum(r['rail_score'] for r in successful_results) / len(successful_results)
    max_score = max(r['rail_score'] for r in successful_results)
    min_score = min(r['rail_score'] for r in successful_results)

    print(f"\nAverage RAIL Score: {avg_score:.2f}/10")
    print(f"Highest Score: {max_score}/10")
    print(f"Lowest Score: {min_score}/10")

    # Grade distribution
    grades = {}
    for r in successful_results:
        grade = r['grade']
        grades[grade] = grades.get(grade, 0) + 1

    print(f"\nGrade Distribution:")
    for grade in ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F']:
        count = grades.get(grade, 0)
        if count > 0:
            bar = '█' * count
            print(f"  {grade}: {bar} ({count})")

    # Domain analysis
    domain_scores = {}
    for r in successful_results:
        domain = r['domain']
        if domain not in domain_scores:
            domain_scores[domain] = []
        domain_scores[domain].append(r['rail_score'])

    print(f"\nAverage Score by Domain:")
    for domain, scores in domain_scores.items():
        avg = sum(scores) / len(scores)
        print(f"  {domain.capitalize()}: {avg:.2f}/10")

# Example 4: Export Results
print("\n" + "=" * 60)
print("Example 4: Export Batch Results")
print("=" * 60)

def export_results_to_csv(results: List[Dict[str, Any]], filename: str):
    """Export results to CSV format."""
    import csv

    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['id', 'domain', 'rail_score', 'grade', 'success', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for r in results:
            writer.writerow({
                'id': r.get('id', ''),
                'domain': r.get('domain', ''),
                'rail_score': r.get('rail_score', ''),
                'grade': r.get('grade', ''),
                'success': r.get('success', False),
                'error': r.get('error', '')
            })

    print(f"\n✓ Results exported to {filename}")

# Uncomment to export results
# export_results_to_csv(results, 'rail_scores_batch.csv')
print("\n(Uncomment export_results_to_csv() to save results to CSV)")

# Example 5: Progress Tracking for Large Batches
print("\n" + "=" * 60)
print("Example 5: Progress Tracking for Large Batches")
print("=" * 60)

def process_with_progress(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process batch with detailed progress tracking."""
    results = []
    total = len(items)
    start_time = time.time()

    print(f"\nProcessing {total} items...")
    print("─" * 60)

    for i, item in enumerate(items, 1):
        item_start = time.time()

        try:
            result = client.calculate(
                content=item['content'],
                domain=item['domain'],
                explain_scores=False  # Faster for batch processing
            )

            results.append({
                'id': item['id'],
                'rail_score': result.rail_score,
                'grade': result.grade,
                'success': True
            })

            status = "✓"

        except Exception as e:
            results.append({
                'id': item['id'],
                'error': str(e),
                'success': False
            })
            status = "✗"

        # Progress bar
        item_time = time.time() - item_start
        elapsed = time.time() - start_time
        avg_time = elapsed / i
        remaining = (total - i) * avg_time

        progress = i / total
        bar_length = 30
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)

        print(f"{status} [{bar}] {i}/{total} ({progress*100:.1f}%) | "
              f"Time: {item_time:.2f}s | ETA: {remaining:.1f}s", end='\r')

    print()  # New line after progress complete
    print("─" * 60)

    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r['success'])

    print(f"\n✓ Batch processing complete!")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Avg time per item: {total_time/total:.2f}s")
    print(f"  Success rate: {success_count}/{total} ({success_count/total*100:.1f}%)")

    return results

# Process first 3 items with progress tracking
progress_results = process_with_progress(content_samples[:3])

print("\n" + "=" * 60)
print("Batch Processing Examples Complete!")
print("=" * 60)
