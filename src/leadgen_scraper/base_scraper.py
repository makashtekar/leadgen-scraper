from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .logging_config import configure_logging
from .rate_limiter import AsyncRateLimiter, RateLimiter
from .user_agents import UserAgentRotator


class BaseScraper(ABC):
    def __init__(
        self,
        requests_per_second: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        configure_logging()
        self.rate_limiter = RateLimiter(requests_per_second)
        self.user_agent_rotator = UserAgentRotator()
        self.max_retries = max_retries
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def _make_request_with_retry(self, url: str, **kwargs) -> httpx.Response:
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            reraise=True,
        )
        def _request():
            self.rate_limiter.wait()
            headers = self.user_agent_rotator.get_headers()
            logger.debug(f"GET {url}")
            return self.client.get(url, headers=headers, **kwargs)

        return _request()

    def get(self, url: str, **kwargs) -> Optional[str]:
        try:
            response = self._make_request_with_retry(url, **kwargs)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            return None
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    @abstractmethod
    def parse(self, html: str) -> list[dict[str, Any]]:
        pass

    def scrape(self, url: str) -> list[dict[str, Any]]:
        html = self.get(url)
        if html:
            return self.parse(html)
        return []

    def close(self) -> None:
        self.client.close()


class AsyncBaseScraper(ABC):
    def __init__(
        self,
        requests_per_second: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        configure_logging()
        self.rate_limiter = AsyncRateLimiter(requests_per_second)
        self.user_agent_rotator = UserAgentRotator()
        self.max_retries = max_retries
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.timeout)
        return self.client

    async def _make_request_with_retry(self, url: str, **kwargs) -> httpx.Response:
        client = await self._get_client()

        async def _request():
            await self.rate_limiter.wait()
            headers = self.user_agent_rotator.get_headers()
            logger.debug(f"GET {url}")
            return await client.get(url, headers=headers, **kwargs)

        for attempt in range(self.max_retries):
            try:
                return await _request()
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == self.max_retries - 1:
                    raise
                wait_time = min(2 ** attempt, 10)
                logger.warning(f"Retry {attempt + 1}/{self.max_retries} for {url}, waiting {wait_time}s")
                import asyncio
                await asyncio.sleep(wait_time)

    async def get(self, url: str, **kwargs) -> Optional[str]:
        try:
            response = await self._make_request_with_retry(url, **kwargs)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}")
            return None
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    @abstractmethod
    async def parse(self, html: str) -> list[dict[str, Any]]:
        pass

    async def scrape(self, url: str) -> list[dict[str, Any]]:
        html = await self.get(url)
        if html:
            return await self.parse(html)
        return []

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
