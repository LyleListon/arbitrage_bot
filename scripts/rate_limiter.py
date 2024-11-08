"""
Rate Limiter for controlling the frequency of operations in the Arbitrage Bot.
"""

import time
from collections import deque


class RateLimiter:
    def __init__(self, max_calls, time_frame):
        self.max_calls = max_calls
        self.time_frame = time_frame
        self.calls = deque()

    def add_call(self):
        current_time = time.time()
        self.calls.append(current_time)

        while self.calls and self.calls[0] <= current_time - self.time_frame:
            self.calls.popleft()

    def is_allowed(self):
        self.add_call()
        return len(self.calls) <= self.max_calls


class RateLimitExceededError(Exception):
    pass


def rate_limit(limiter):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if limiter.is_allowed():
                return func(*args, **kwargs)
            else:
                raise RateLimitExceededError(
                    "Rate limit exceeded. Please try again later."
                )
        return wrapper
    return decorator


# Usage example:
# trade_limiter = RateLimiter(max_calls=5, time_frame=60)  # 5 calls per minute
#
# @rate_limit(trade_limiter)
# def execute_trade():
#     # Trade execution logic here
#     pass
