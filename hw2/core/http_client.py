from typing import Any

import httpx
from httpx import Response

from hw2.core.exceptions import HttpError


class HttpClient:
    def __init__(self, headers: dict[str, Any] | None = None, default_timeout: float= 10.0) -> None:
        self.default_timeout = default_timeout

        if headers is None:
            self.headers = {"User-Agent": "Mozilla/5.0"}
        else:
            self.headers = headers

        self.client = httpx.Client(timeout=self.default_timeout, headers=self.headers)

    def get(self, url: str, **kwargs) -> Response:
        with self.client as client:
            try:
                response = client.get(url=url, **kwargs)
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                raise HttpError(
                    status=err.response.status_code,
                    url=str(err.request.url),
                ) from err

            return response