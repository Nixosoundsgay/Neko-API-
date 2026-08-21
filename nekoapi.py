import time
import logging
import requests
from typing import Optional, List, Dict, Any, Union
from functools import lru_cache
from datetime import datetime, timedelta


class NekoAPIError(Exception):
    """Base exception for NekoAPI"""
    pass


class RateLimitError(NekoAPIError):
    """Raised when the API rate limits us"""
    pass


class APIConnectionError(NekoAPIError):
    """Raised when we can't connect to the API"""
    pass


class NekoAPI:
    BASE_URL = "https://catfact.ninja"
    DEFAULT_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 1.5

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        user_agent: Optional[str] = None,
        enable_cache: bool = True
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self._session = requests.Session()
        
        headers = {
            "Accept": "application/json",
            "User-Agent": user_agent or "NekoAPI/1.0"
        }
        self._session.headers.update(headers)

        self._cache = {}
        self._cache_ttl = timedelta(minutes=5)

        self.logger = logging.getLogger("NekoAPI")

    def _is_cache_valid(self, key: str) -> bool:
        if not self.enable_cache or key not in self._cache:
            return False
        timestamp, _ = self._cache[key]
        return datetime.now() - timestamp < self._cache_ttl

    def _get_from_cache(self, key: str) -> Any:
        return self._cache[key][1]

    def _set_cache(self, key: str, value: Any) -> None:
        if self.enable_cache:
            self._cache[key] = (datetime.now(), value)

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )

                if response.status_code == 429:
                    raise RateLimitError("Rate limited by the API")

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout as e:
                last_exception = e
                self.logger.warning(f"Timeout on attempt {attempt}/{self.max_retries}")
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                self.logger.warning(f"Connection error on attempt {attempt}/{self.max_retries}")
            except requests.exceptions.HTTPError as e:
                raise APIConnectionError(f"HTTP error: {e}")
            except RateLimitError:
                raise
            except Exception as e:
                last_exception = e
                self.logger.error(f"Unexpected error: {e}")

            if attempt < self.max_retries:
                time.sleep(self.RETRY_DELAY * attempt)

        raise APIConnectionError(f"Failed after {self.max_retries} retries: {last_exception}")

    def get_fact(self, max_length: Optional[int] = None, use_cache: bool = True) -> str:
        cache_key = f"fact:{max_length}"

        if use_cache and self._is_cache_valid(cache_key):
            return self._get_from_cache(cache_key)

        params = {}
        if max_length is not None:
            params["max_length"] = max_length

        data = self._request("/fact", params)
        fact = data.get("fact")

        if not fact:
            raise NekoAPIError("No fact returned from API")

        self._set_cache(cache_key, fact)
        return fact

    def get_facts(
        self,
        limit: int = 5,
        max_length: Optional[int] = None,
        use_cache: bool = True
    ) -> List[str]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        cache_key = f"facts:{limit}:{max_length}"

        if use_cache and self._is_cache_valid(cache_key):
            return self._get_from_cache(cache_key)

        params = {"limit": limit}
        if max_length is not None:
            params["max_length"] = max_length

        data = self._request("/facts", params)
        facts = [item["fact"] for item in data.get("data", []) if "fact" in item]

        self._set_cache(cache_key, facts)
        return facts

    def get_breeds(self, limit: int = 10, use_cache: bool = True) -> List[Dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        cache_key = f"breeds:{limit}"

        if use_cache and self._is_cache_valid(cache_key):
            return self._get_from_cache(cache_key)

        data = self._request("/breeds", {"limit": limit})
        breeds = data.get("data", [])

        self._set_cache(cache_key, breeds)
        return breeds

    def clear_cache(self) -> None:
        """Clear the internal cache"""
        self._cache.clear()

    def close(self) -> None:
        """Close the underlying session"""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    with NekoAPI() as neko:
        print("Single fact:")
        print(neko.get_fact())
        print("\nMultiple facts:")
        for fact in neko.get_facts(3):
            print(f"- {fact}")
