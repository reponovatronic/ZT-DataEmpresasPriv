from __future__ import annotations

import requests

from .base import SearchProvider


class SerperProvider(SearchProvider):
    name = "serper"

    def __init__(
        self,
        api_key,
        country="pe",
        language="es",
        timeout=30,
    ):
        self.api_key = api_key
        self.country = country
        self.language = language
        self.timeout = timeout

    def search(self, query, max_results=10):
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "q": query,
                "gl": self.country,
                "hl": self.language,
                "num": max_results,
            },
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Serper HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        data = response.json()
        results = []

        for i, item in enumerate(
            data.get("organic", []) or [],
            start=1,
        ):
            results.append(
                {
                    "position": item.get("position", i),
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "displayed_link": item.get("displayedLink", ""),
                }
            )

        return results[:max_results]
