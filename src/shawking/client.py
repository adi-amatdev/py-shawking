"""Client interface for the Shawking REST service."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib import error, request

JsonResponse = dict[str, Any] | list[Any]
_UNSET = object()
_ALLOWED_SCHEMES = {"http", "https"}


def _normalize_reference_time(value: int | datetime) -> int:
    """Convert a datetime into epoch milliseconds when needed."""
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    return value


@dataclass(slots=True)
class ShawkingConfig:
    """Default request options applied to every parse call."""

    time_zone: str | None = None
    reference_time: int | datetime | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def as_payload(self) -> dict[str, Any]:
        """Render the config as a Shawking API payload fragment."""
        payload: dict[str, Any] = {}

        if self.time_zone is not None:
            payload["timeZone"] = self.time_zone

        if self.reference_time is not None:
            payload["referenceTime"] = _normalize_reference_time(self.reference_time)

        payload.update({key: value for key, value in self.extra.items() if value is not None})
        return payload


class ShawkingClientError(RuntimeError):
    """Raised when the Shawking service cannot be reached or returns an invalid response."""


class ShawkingClient:
    """Class-based client for a running Shawking REST service.

    Args:
        ip: Hostname or IP address where Shawking is running.
        port: Port exposed by the Shawking service.
        scheme: URL scheme, usually ``http``.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        ip: str = "127.0.0.1",
        port: int = 8080,
        *,
        scheme: str = "http",
        timeout: float = 30.0,
    ) -> None:
        if scheme not in _ALLOWED_SCHEMES:
            msg = f"`scheme` must be one of {_ALLOWED_SCHEMES}, got {scheme!r}."
            raise ValueError(msg)

        self.ip = ip
        self.port = port
        self.scheme = scheme
        self.timeout = timeout
        self._config = ShawkingConfig()

    @property
    def base_url(self) -> str:
        """Service root URL."""
        return f"{self.scheme}://{self.ip}:{self.port}"

    def config(
        self,
        *,
        time_zone: str | None | object = _UNSET,
        reference_time: int | datetime | None | object = _UNSET,
        **options: Any,
    ) -> ShawkingClient:
        """Set or update default request options for future parse calls.

        ``time_zone`` and ``reference_time`` are first-class convenience fields.
        Any extra keyword arguments are forwarded to the Shawking API as-is.
        Passing ``None`` removes an existing default for that field.
        """
        if time_zone is not _UNSET:
            self._config.time_zone = time_zone

        if reference_time is not _UNSET:
            self._config.reference_time = reference_time

        for key, value in options.items():
            if value is None:
                self._config.extra.pop(key, None)
            else:
                self._config.extra[key] = value

        return self

    def parse(
        self,
        text: str,
        *,
        time_zone: str | None | object = _UNSET,
        reference_time: int | datetime | None | object = _UNSET,
        **overrides: Any,
    ) -> JsonResponse:
        """Parse natural-language text into Shawking date results.

        Per-call overrides take precedence over values configured via :meth:`config`.
        Passing ``None`` for an override removes the configured default for that request.
        """
        if not text or not text.strip():
            msg = "`text` must be a non-empty string."
            raise ValueError(msg)

        payload = {"text": text, **self._config.as_payload()}

        if time_zone is not _UNSET:
            if time_zone is None:
                payload.pop("timeZone", None)
            else:
                payload["timeZone"] = time_zone

        if reference_time is not _UNSET:
            if reference_time is None:
                payload.pop("referenceTime", None)
            else:
                payload["referenceTime"] = _normalize_reference_time(reference_time)

        for key, value in overrides.items():
            if value is None:
                payload.pop(key, None)
            else:
                payload[key] = value

        return self._post("/parse", payload)

    def _post(self, path: str, payload: dict[str, Any]) -> JsonResponse:
        data = json.dumps(payload).encode("utf-8")
        # `scheme` is validated in `__init__`, so this request is limited to HTTP(S).
        http_request = request.Request(  # noqa: S310
            url=f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:  # noqa: S310
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            msg = f"Shawking request failed with status {exc.code}: {body}"
            raise ShawkingClientError(msg) from exc
        except error.URLError as exc:
            msg = f"Could not reach Shawking service at {self.base_url}: {exc.reason}"
            raise ShawkingClientError(msg) from exc

        try:
            parsed_response = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            msg = "Shawking service returned invalid JSON."
            raise ShawkingClientError(msg) from exc

        if not isinstance(parsed_response, (dict, list)):
            msg = "Shawking service returned an unexpected payload type."
            raise ShawkingClientError(msg)

        return parsed_response
