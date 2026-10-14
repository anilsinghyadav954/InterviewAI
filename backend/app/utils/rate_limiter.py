import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """
    Lightweight, in-memory sliding window rate limiter.
    Zero infrastructure dependencies (no Redis required).
    Tracks timestamps per key (e.g., user_id or IP) and expires old entries.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60, name: str = "default"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, key: str) -> None:
        """
        Records an attempt for `key`. Raises HTTP 429 if the limit is exceeded.
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Prune timestamps older than the sliding window
        window_hits = [t for t in self.requests[key] if t > cutoff]
        self.requests[key] = window_hits

        if len(window_hits) >= self.max_requests:
            logger.warning(
                f"Rate limit exceeded on '{self.name}' for key '{key}': "
                f"{len(window_hits)} requests in {self.window_seconds}s (limit: {self.max_requests})"
            )
            retry_after = int(window_hits[0] + self.window_seconds - now) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Too many requests for {self.name}. Please wait {max(1, retry_after)} seconds before trying again.",
                headers={"Retry-After": str(max(1, retry_after))},
            )

        # Record this request
        self.requests[key].append(now)

    def reset(self, key: str = None) -> None:
        """Helper to clear rate limit state (useful for tests)."""
        if key:
            self.requests.pop(key, None)
        else:
            self.requests.clear()


# Pre-configured limiters for AI-intensive operations
# Resume Analysis: max 15 analyses per minute
resume_limiter = SlidingWindowRateLimiter(max_requests=15, window_seconds=60, name="Resume Analysis")

# Question Generation: max 20 generations per minute
question_gen_limiter = SlidingWindowRateLimiter(max_requests=20, window_seconds=60, name="Question Generation")

# Answer Evaluation (Text & Voice): max 45 evaluations per minute
evaluation_limiter = SlidingWindowRateLimiter(max_requests=45, window_seconds=60, name="Answer Evaluation")

# Forgot Password requests: max 5 requests per minute per IP / target
forgot_password_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60, name="Password Reset Request")
