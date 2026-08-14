"""Minimal Upstash Redis REST client used by Vercel Functions."""
from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class UpstashRedis:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"}

    @classmethod
    def from_settings(cls) -> "UpstashRedis | None":
        url = settings.resolved_upstash_redis_rest_url
        token = settings.resolved_upstash_redis_rest_token
        if not url or not token:
            return None
        return cls(url, token)

    async def command(self, *parts: object) -> Any:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(self.url, headers=self.headers, json=list(parts))
            response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        return payload.get("result")

    async def pipeline(self, commands: list[list[object]]) -> list[Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{self.url}/pipeline", headers=self.headers, json=commands)
            response.raise_for_status()
        payload = response.json()
        results: list[Any] = []
        for item in payload:
            if item.get("error"):
                raise RuntimeError(item["error"])
            results.append(item.get("result"))
        return results
