"""Shared retry handling for temporary Mistral API rate limits."""

import random
import time


def invoke_with_rate_limit_retry(chain, value, *, attempts: int = 5):
    """Retry 429 responses with exponential backoff; re-raise other errors."""
    for attempt in range(attempts):
        try:
            return chain.invoke(value)
        except Exception as exc:
            message = str(exc).lower()
            status = getattr(exc, "status_code", None)
            response = getattr(exc, "response", None)
            if status is None and response is not None:
                status = getattr(response, "status_code", None)
            limited = status == 429 or "rate limit exceeded" in message or "rate_limited" in message
            if not limited or attempt == attempts - 1:
                raise

            retry_after = None
            headers = getattr(response, "headers", None)
            if headers:
                try:
                    retry_after = float(headers.get("Retry-After"))
                except (TypeError, ValueError):
                    pass
            delay = retry_after or min(60, 5 * (2 ** attempt))
            time.sleep(delay + random.uniform(0, 1))
