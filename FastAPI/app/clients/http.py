from __future__ import annotations
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional
import requests

logger = logging.getLogger(__name__)

class UpstreamTimeoutError(Exception):
    """Timeout/ConnectionError при обращении к upstream."""

class UpstreamHTTPError(Exception):
    """Upstream вернул HTTP-статус, который мы считаем ошибкой (например, 5xx)."""

    def __init__(self, status_code: int, response_text: str | None = None):
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(f"Upstream HTTP error: {status_code}")

@dataclass(frozen=True)
class HttpClientConfig:
    timeout: float
    retries: int
    backoff: float

class HttpClient:
    """ Обёртка над requests.Session:
    - timeout обязателен
    - ретраи: только сетевые исключения и 5xx
    - 4xx не ретраим
    - логируем метод, url, статус, elapsed_ms """

    def __init__(self, session: requests.Session, config: HttpClientConfig):
        self._session = session
        self._config = config

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> requests.Response:
        last_exc: Exception | None = None

        # retries=3 означает "всего 3 попытки"
        attempts = max(1, int(self._config.retries))

        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            status_code: int | None = None

            try:
                resp = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    timeout=self._config.timeout,
                )
                status_code = resp.status_code

                elapsed_ms = int((time.perf_counter() - started) * 1000)
                logger.info(
                    "upstream_request method=%s url=%s status=%s elapsed_ms=%s attempt=%s/%s",
                    method,
                    url,
                    status_code,
                    elapsed_ms,
                    attempt,
                    attempts,
                )

                # 5xx -> ретраим (до исчерпания попыток)
                if 500 <= resp.status_code <= 599:
                    last_exc = UpstreamHTTPError(resp.status_code, response_text=resp.text)
                    if attempt < attempts:
                        self._sleep_backoff(attempt)
                        continue
                    raise last_exc

                # 4xx не ретраим, возвращаем как есть (решит сервисный слой)
                return resp

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                logger.warning(
                    "upstream_request_failed method=%s url=%s elapsed_ms=%s attempt=%s/%s error=%s",
                    method,
                    url,
                    elapsed_ms,
                    attempt,
                    attempts,
                    exc.__class__.__name__,
                )
                last_exc = exc
                if attempt < attempts:
                    self._sleep_backoff(attempt)
                    continue
                raise UpstreamTimeoutError(str(exc)) from exc

        # теоретически сюда не попадём
        raise UpstreamTimeoutError(str(last_exc) if last_exc else "Unknown upstream error")

    def _sleep_backoff(self, attempt: int) -> None:
        # Простой линейный backoff: backoff * attempt
        delay = float(self._config.backoff) * attempt
        if delay > 0:
            time.sleep(delay)
