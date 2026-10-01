from __future__ import annotations

import requests

from .base import SearchProvider


class ExaProvider(SearchProvider):
    name = "exa"

    def __init__(self, api_key, timeout=45):
        self.api_key = api_key
        self.timeout = timeout

    def search(self, query, max_results=10):
        response = requests.post(
            "https://api.exa.ai/search",
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "type": "auto",
                "numResults": max_results,
            },
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Exa HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        data = response.json()
        results = []

        for i, item in enumerate(
            data.get("results", []) or [],
            start=1,
        ):
            results.append(
                {
                    "position": i,
                    "title": item.get("title", ""),
                    "link": item.get("url", ""),
                    "snippet": item.get("text", "") or "",
                    "displayed_link": item.get("url", ""),
                }
            )

        return results[:max_results]
