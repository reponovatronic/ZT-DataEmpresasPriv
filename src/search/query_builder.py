from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path

import pandas as pd
import yaml


class QueryBuilder:

    def __init__(
        self,
        config_path="config/niches.yaml",
        processed_root="data/processed",
        cache_root="data/cache",
    ):
        self.config_path = Path(config_path)
        self.processed_root = Path(processed_root)
        self.cache_root = Path(cache_root)

    @staticmethod
    def normalize(value):
        return re.sub(
            r"\s+",
            " ",
            str(value).strip().lower(),
        )

    def make_key(self, niche_id, query):
        raw = (
            f"{self.normalize(niche_id)}|"
            f"{self.normalize(query)}"
        )

        return hashlib.sha1(
            raw.encode("utf-8")
        ).hexdigest()

    def load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(self.config_path)

        with open(
            self.config_path,
            "r",
            encoding="utf-8",
        ) as f:
            return yaml.safe_load(f) or {}

    def run(self, niche=None):
        config = self.load_config()

        rows = []

        for niche_id, cfg in config.get("niches", {}).items():

            if not cfg.get("enabled", False):
                continue

            if niche and niche_id != niche:
                continue

            niche_name = cfg.get(
                "name",
                niche_id,
            )

            country = cfg.get(
                "country",
                "Perú",
            )

            keywords = cfg.get(
                "keywords",
                [],
            ) or []

            for position, query in enumerate(
                keywords,
                start=1,
            ):
                query = str(query).strip()

                if not query:
                    continue

                rows.append(
                    {
                        "BASE_QUERY_KEY":
                            self.make_key(
                                niche_id,
                                query,
                            ),
                        "NICHE_ID":
                            niche_id,
                        "NICHE_NAME":
                            niche_name,
                        "COUNTRY":
                            country,
                        "QUERY_TYPE":
                            "DISCOVERY",
                        "QUERY_POSITION":
                            position,
                        "QUERY":
                            query,
                    }
                )

        df = pd.DataFrame(rows)

        if df.empty:
            raise RuntimeError(
                "No se generaron queries. Revisa config/niches.yaml"
            )

        df = df.drop_duplicates(
            subset=["BASE_QUERY_KEY"],
            keep="first",
        )

        folder = (
            self.processed_root
            / date.today().isoformat()
        )

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.cache_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        dated_path = (
            folder
            / "search_queries.csv"
        )

        cache_path = (
            self.cache_root
            / "search_queries.csv"
        )

        df.to_csv(
            dated_path,
            index=False,
            encoding="utf-8-sig",
        )

        df.to_csv(
            cache_path,
            index=False,
            encoding="utf-8-sig",
        )

        print("=" * 70)
        print(" QUERY BUILDER")
        print("=" * 70)
        print(f"Nichos  : {df['NICHE_ID'].nunique():,}")
        print(f"Queries : {len(df):,}")
        print()

        print(
            df[
                [
                    "NICHE_ID",
                    "QUERY_POSITION",
                    "QUERY",
                ]
            ].to_string(index=False)
        )

        print()
        print(dated_path)
        print(cache_path)
        print("=" * 70)

        return cache_path
