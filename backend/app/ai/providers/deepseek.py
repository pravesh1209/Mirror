"""DeepSeek chat-completions client.

Two retries. Strict JSON mode. Any failure returns None so the caller can
fall back. Never raises.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel

from ...config import settings
from ..base import ProviderHealth
from ..json_repair import parse_and_validate

log = logging.getLogger("mirror.ai.deepseek")
T = TypeVar("T", bound=BaseModel)


class DeepSeekProvider:
    name = "deepseek"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.deepseek_api_key
        self.base_url = (base_url or settings.deepseek_base_url).rstrip("/")
        self.model = model or settings.deepseek_model
        self._last_error: str | None = None

    async def _call(
        self,
        *,
        system: str,
        user: str,
        timeout_s: float,
        json_mode: bool,
    ) -> str | None:
        if not self.api_key:
            self._last_error = "missing api key"
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.7,
            "max_tokens": 1500,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        url = f"{self.base_url}/chat/completions"

        for attempt in (1, 2, 3):
            try:
                async with httpx.AsyncClient(timeout=timeout_s) as client:
                    r = await client.post(url, headers=headers, json=payload)
                if r.status_code >= 500:
                    raise httpx.HTTPError(f"upstream {r.status_code}")
                if r.status_code >= 400:
                    # 4xx: don't retry
                    self._last_error = f"http {r.status_code}: {r.text[:200]}"
                    log.warning("deepseek 4xx: %s", self._last_error)
                    return None
                body = r.json()
                content = (
                    body.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                if not content:
                    raise ValueError("empty content")
                self._last_error = None
                return content
            except (httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError) as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                log.warning("deepseek attempt %d failed: %s", attempt, self._last_error)
                if attempt < 3:
                    await asyncio.sleep(0.5 * attempt)
            except Exception as exc:
                self._last_error = f"{type(exc).__name__}: {exc}"
                log.exception("deepseek unexpected error")
                return None

        return None

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        timeout_s: float = 20.0,
    ) -> T | None:
        schema_hint = self._schema_hint(schema)
        system_full = f"{system}\n\n{schema_hint}"

        for attempt in (1, 2):
            raw = await self._call(
                system=system_full, user=user, timeout_s=timeout_s, json_mode=True
            )
            if not raw:
                return None
            parsed = parse_and_validate(raw, schema)
            if parsed is not None:
                return parsed
            log.warning("deepseek returned invalid JSON for %s (attempt %d)", schema.__name__, attempt)
            # on retry, nudge with a stricter instruction
            system_full = (
                system
                + "\n\nReturn ONLY a single JSON object. No prose. No markdown. "
                + self._schema_hint(schema)
            )

        return None

    async def complete_text(
        self,
        *,
        system: str,
        user: str,
        timeout_s: float = 20.0,
    ) -> str | None:
        return await self._call(system=system, user=user, timeout_s=timeout_s, json_mode=False)

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            name=self.name,
            available=bool(self.api_key),
            last_error=self._last_error,
        )

    @staticmethod
    def _schema_hint(schema: type[BaseModel]) -> str:
        """Render a compact JSON-shape hint for the model."""
        try:
            js = schema.model_json_schema()
        except Exception:
            return "Return a JSON object matching the described fields."
        # Compact: top-level required fields + type names
        props = js.get("properties", {}) or {}
        lines = ["Return a JSON object with these fields:"]
        for name, spec in props.items():
            typ = spec.get("type") or spec.get("anyOf") or "any"
            lines.append(f'  "{name}": {typ}')
        return "\n".join(lines)


__all__ = ["DeepSeekProvider"]