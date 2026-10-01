from __future__ import annotations

from abc import ABC, abstractmethod


class SearchProvider(ABC):
    name = "base"

    @abstractmethod
    def search(self, query: str, max_results: int = 10):
        raise NotImplementedError
