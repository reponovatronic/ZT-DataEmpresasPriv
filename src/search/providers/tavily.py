from __future__ import annotations

import requests

from .base import SearchProvider


class TavilyProvider(SearchProvider):
    name = "tavily"

    def __init__(self, api_key, timeout=40):
        self.api_key = api_key
        self.timeout = timeout

    def search(self, query, max_results=10):
        response = requests.post(
            "https://api.tavily.com/search",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
                "include_images": False,
                "include_raw_content": False,
            },
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Tavily HTTP {response.status_code}: "
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
                    "snippet": item.get("content", ""),
                    "displayed_link": item.get("url", ""),
                }
            )

        return results[:max_results]
