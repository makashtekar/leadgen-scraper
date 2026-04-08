import asyncio
import time
from threading import Lock
from typing import Optional


class RateLimiter:
    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self._last_request_time: Optional[float] = None
        self._lock = Lock()

    def wait(self) -> None:
        with self._lock:
            current_time = time.time()
            if self._last_request_time is not None:
                elapsed = current_time - self._last_request_time
                if elapsed < self.min_interval:
                    sleep_time = self.min_interval - elapsed
                    time.sleep(sleep_time)
            self._last_request_time = time.time()


class AsyncRateLimiter:
    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self._last_request_time: Optional[float] = None
        self._lock: Optional[asyncio.Lock] = None

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def wait(self) -> None:
        lock = await self._get_lock()
        async with lock:
            current_time = time.time()
            if self._last_request_time is not None:
                elapsed = current_time - self._last_request_time
                if elapsed < self.min_interval:
                    sleep_time = self.min_interval - elapsed
                    await asyncio.sleep(sleep_time)
            self._last_request_time = time.time()
