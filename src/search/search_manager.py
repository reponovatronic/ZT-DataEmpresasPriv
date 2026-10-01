from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

from src.search.providers.serper import SerperProvider
from src.search.providers.tavily import TavilyProvider
from src.search.providers.exa import ExaProvider


class SearchManager:

    def __init__(
        self,
        queries_path="data/cache/search_queries.csv",
        cache_root="data/cache",
        config_path="config/search_providers.yaml",
        delay_seconds=0.30,
    ):
        load_dotenv(
            dotenv_path=".env",
            override=True,
        )

        self.queries_path = Path(queries_path)
        self.cache_root = Path(cache_root)
        self.config_path = Path(config_path)
        self.delay_seconds = delay_seconds

        self.config = self.load_config()

        search_cfg = self.config.get(
            "search",
            {},
        )

        self.max_results = int(
            search_cfg.get(
                "max_results",
                10,
            )
        )

        self.country = search_cfg.get(
            "country",
            "pe",
        )

        self.language = search_cfg.get(
            "language",
            "es",
        )

        self.fallback_on_error = bool(
            search_cfg.get(
                "fallback_on_error",
                True,
            )
        )

        self.fallback_on_no_results = bool(
            search_cfg.get(
                "fallback_on_no_results",
                True,
            )
        )

    def load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(
                self.config_path
            )

        with open(
            self.config_path,
            "r",
            encoding="utf-8",
        ) as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def sha1(value):
        return hashlib.sha1(
            str(value).encode("utf-8")
        ).hexdigest()

    def provider_query_key(
        self,
        provider,
        base_query_key,
    ):
        return self.sha1(
            f"{provider.lower()}|{base_query_key}"
        )

    # =========================================================
    # PROVIDERS
    # =========================================================

    def get_providers(self):
        providers_cfg = self.config.get(
            "providers",
            {},
        )

        available = []
        missing = []

        for name, cfg in providers_cfg.items():

            if not cfg.get(
                "enabled",
                False,
            ):
                continue

            env_name = cfg.get(
                "api_key_env",
                "",
            )

            api_key = os.getenv(
                env_name,
                "",
            ).strip()

            item = {
                "name": name.lower(),
                "priority": int(
                    cfg.get(
                        "priority",
                        999,
                    )
                ),
                "env_name": env_name,
                "api_key": api_key,
            }

            if api_key:
                available.append(item)
            else:
                missing.append(item)

        available.sort(
            key=lambda x: x["priority"]
        )

        return available, missing

    def build_provider(self, item):
        name = item["name"]

        if name == "serper":
            return SerperProvider(
                api_key=item["api_key"],
                country=self.country,
                language=self.language,
            )

        if name == "tavily":
            return TavilyProvider(
                api_key=item["api_key"],
            )

        if name == "exa":
            return ExaProvider(
                api_key=item["api_key"],
            )

        raise RuntimeError(
            f"Proveedor no implementado: {name}"
        )

    # =========================================================
    # FILES
    # =========================================================

    def result_path(self):
        self.cache_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        return (
            self.cache_root
            / "search_results.csv"
        )

    def run_log_path(self):
        return (
            self.cache_root
            / "search_run_log.csv"
        )

    def load_queries(self, niche=None):
        if not self.queries_path.exists():
            raise FileNotFoundError(
                "No existe data/cache/search_queries.csv. "
                "Ejecuta primero build-queries."
            )

        df = pd.read_csv(
            self.queries_path,
            dtype=str,
            keep_default_na=False,
        )

        if niche:
            df = df[
                df["NICHE_ID"] == niche
            ].copy()

        return df

    def load_existing(self):
        path = self.result_path()

        columns = [
            "BASE_QUERY_KEY",
            "QUERY_KEY",
            "NICHE_ID",
            "NICHE_NAME",
            "QUERY_TYPE",
            "QUERY",
            "PROVIDER",
            "PROVIDER_ATTEMPT",
            "STATUS",
            "POSITION",
            "TITLE",
            "LINK",
            "SNIPPET",
            "DISPLAYED_LINK",
            "ERROR",
            "SEARCHED_AT",
        ]

        if not path.exists():
            return pd.DataFrame(
                columns=columns
            )

        df = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
        )

        for col in columns:
            if col not in df.columns:
                df[col] = ""

        return df

    def completed_keys(self, existing):
        if existing.empty:
            return set()

        completed = existing[
            existing["STATUS"]
            .astype(str)
            .str.upper()
            .isin(
                [
                    "OK",
                    "NO_RESULTS_FINAL",
                ]
            )
        ]

        return set(
            completed[
                "BASE_QUERY_KEY"
            ]
            .astype(str)
            .tolist()
        )

    def save_results(self, df):
        if df.empty:
            df.to_csv(
                self.result_path(),
                index=False,
                encoding="utf-8-sig",
            )
            return df

        has_link = (
            df["LINK"]
            .astype(str)
            .str.strip()
            .ne("")
        )

        with_link = df[
            has_link
        ].copy()

        without_link = df[
            ~has_link
        ].copy()

        if not with_link.empty:
            with_link = (
                with_link
                .drop_duplicates(
                    subset=[
                        "BASE_QUERY_KEY",
                        "PROVIDER",
                        "LINK",
                    ],
                    keep="first",
                )
            )

        if not without_link.empty:
            without_link = (
                without_link
                .drop_duplicates(
                    subset=[
                        "BASE_QUERY_KEY",
                        "PROVIDER",
                        "STATUS",
                    ],
                    keep="last",
                )
            )

        final = pd.concat(
            [
                with_link,
                without_link,
            ],
            ignore_index=True,
        )

        final.to_csv(
            self.result_path(),
            index=False,
            encoding="utf-8-sig",
        )

        return final

    # =========================================================
    # RUN
    # =========================================================

    def run(
        self,
        niche=None,
        limit_queries=None,
    ):
        queries = self.load_queries(
            niche=niche
        )

        existing = self.load_existing()

        completed = self.completed_keys(
            existing
        )

        queries["IS_CACHED"] = (
            queries["BASE_QUERY_KEY"]
            .isin(completed)
        )

        pending = queries[
            ~queries["IS_CACHED"]
        ].copy()

        if limit_queries is not None:
            pending = pending.head(
                limit_queries
            )

        provider_configs, missing = (
            self.get_providers()
        )

        if not provider_configs:
            raise RuntimeError(
                "No hay proveedores activos con API key."
            )

        providers = [
            (
                cfg,
                self.build_provider(cfg),
            )
            for cfg in provider_configs
        ]

        print("=" * 70)
        print(
            " SEARCH MANAGER - MULTIPROVEEDOR INCREMENTAL"
        )
        print("=" * 70)

        print(
            "Proveedores activos : "
            + ", ".join(
                p["name"]
                for p in provider_configs
            )
        )

        if missing:
            print(
                "Sin API key          : "
                + ", ".join(
                    f"{p['name']}({p['env_name']})"
                    for p in missing
                )
            )

        print(
            f"Queries totales     : {len(queries):,}"
        )

        print(
            f"Queries en cache    : "
            f"{queries['IS_CACHED'].sum():,}"
        )

        print(
            f"Queries a ejecutar  : {len(pending):,}"
        )

        print(
            f"Resultados existentes: {len(existing):,}"
        )

        print("-" * 70)

        new_rows = []

        api_calls = {
            p["name"]: 0
            for p in provider_configs
        }

        success = {
            p["name"]: 0
            for p in provider_configs
        }

        errors = {
            p["name"]: 0
            for p in provider_configs
        }

        no_results = {
            p["name"]: 0
            for p in provider_configs
        }

        total = len(pending)

        for number, row in enumerate(
            pending.itertuples(index=False),
            start=1,
        ):
            r = row._asdict()

            base_key = r["BASE_QUERY_KEY"]
            query = r["QUERY"]
            niche_id = r["NICHE_ID"]
            niche_name = r["NICHE_NAME"]
            query_type = r.get(
                "QUERY_TYPE",
                "DISCOVERY",
            )

            print(
                f"[{number}/{total}] "
                f"{niche_id} | {query}"
            )

            solved = False
            all_no_results = True

            for attempt, (
                provider_cfg,
                provider,
            ) in enumerate(
                providers,
                start=1,
            ):
                provider_name = (
                    provider_cfg["name"]
                )

                print(
                    f"  -> intentando {provider_name}"
                )

                query_key = (
                    self.provider_query_key(
                        provider_name,
                        base_key,
                    )
                )

                searched_at = (
                    datetime.now()
                    .isoformat(
                        timespec="seconds"
                    )
                )

                try:
                    api_calls[
                        provider_name
                    ] += 1

                    results = provider.search(
                        query,
                        max_results=self.max_results,
                    )

                    if results:
                        solved = True
                        all_no_results = False

                        success[
                            provider_name
                        ] += 1

                        print(
                            f"     OK: {len(results)} resultados"
                        )

                        for result in results:
                            new_rows.append(
                                {
                                    "BASE_QUERY_KEY":
                                        base_key,
                                    "QUERY_KEY":
                                        query_key,
                                    "NICHE_ID":
                                        niche_id,
                                    "NICHE_NAME":
                                        niche_name,
                                    "QUERY_TYPE":
                                        query_type,
                                    "QUERY":
                                        query,
                                    "PROVIDER":
                                        provider_name,
                                    "PROVIDER_ATTEMPT":
                                        attempt,
                                    "STATUS":
                                        "OK",
                                    "POSITION":
                                        result.get(
                                            "position",
                                            "",
                                        ),
                                    "TITLE":
                                        result.get(
                                            "title",
                                            "",
                                        ),
                                    "LINK":
                                        result.get(
                                            "link",
                                            "",
                                        ),
                                    "SNIPPET":
                                        result.get(
                                            "snippet",
                                            "",
                                        ),
                                    "DISPLAYED_LINK":
                                        result.get(
                                            "displayed_link",
                                            "",
                                        ),
                                    "ERROR":
                                        "",
                                    "SEARCHED_AT":
                                        searched_at,
                                }
                            )

                        break

                    no_results[
                        provider_name
                    ] += 1

                    print(
                        "     sin resultados"
                    )

                    new_rows.append(
                        {
                            "BASE_QUERY_KEY":
                                base_key,
                            "QUERY_KEY":
                                query_key,
                            "NICHE_ID":
                                niche_id,
                            "NICHE_NAME":
                                niche_name,
                            "QUERY_TYPE":
                                query_type,
                            "QUERY":
                                query,
                            "PROVIDER":
                                provider_name,
                            "PROVIDER_ATTEMPT":
                                attempt,
                            "STATUS":
                                "NO_RESULTS",
                            "POSITION":
                                "",
                            "TITLE":
                                "",
                            "LINK":
                                "",
                            "SNIPPET":
                                "",
                            "DISPLAYED_LINK":
                                "",
                            "ERROR":
                                "",
                            "SEARCHED_AT":
                                searched_at,
                        }
                    )

                    if not self.fallback_on_no_results:
                        break

                except Exception as exc:
                    all_no_results = False

                    errors[
                        provider_name
                    ] += 1

                    print(
                        f"     ERROR: {str(exc)[:250]}"
                    )

                    new_rows.append(
                        {
                            "BASE_QUERY_KEY":
                                base_key,
                            "QUERY_KEY":
                                query_key,
                            "NICHE_ID":
                                niche_id,
                            "NICHE_NAME":
                                niche_name,
                            "QUERY_TYPE":
                                query_type,
                            "QUERY":
                                query,
                            "PROVIDER":
                                provider_name,
                            "PROVIDER_ATTEMPT":
                                attempt,
                            "STATUS":
                                "ERROR",
                            "POSITION":
                                "",
                            "TITLE":
                                "",
                            "LINK":
                                "",
                            "SNIPPET":
                                "",
                            "DISPLAYED_LINK":
                                "",
                            "ERROR":
                                str(exc),
                            "SEARCHED_AT":
                                searched_at,
                        }
                    )

                    if not self.fallback_on_error:
                        break

                finally:
                    current = pd.concat(
                        [
                            existing,
                            pd.DataFrame(
                                new_rows
                            ),
                        ],
                        ignore_index=True,
                    )

                    self.save_results(
                        current
                    )

                    time.sleep(
                        self.delay_seconds
                    )

            if (
                not solved
                and all_no_results
            ):
                new_rows.append(
                    {
                        "BASE_QUERY_KEY":
                            base_key,
                        "QUERY_KEY":
                            self.sha1(
                                f"final|{base_key}"
                            ),
                        "NICHE_ID":
                            niche_id,
                        "NICHE_NAME":
                            niche_name,
                        "QUERY_TYPE":
                            query_type,
                        "QUERY":
                            query,
                        "PROVIDER":
                            "system",
                        "PROVIDER_ATTEMPT":
                            "",
                        "STATUS":
                            "NO_RESULTS_FINAL",
                        "POSITION":
                            "",
                        "TITLE":
                            "",
                        "LINK":
                            "",
                        "SNIPPET":
                            "",
                        "DISPLAYED_LINK":
                            "",
                        "ERROR":
                            "",
                        "SEARCHED_AT":
                            datetime.now()
                            .isoformat(
                                timespec="seconds"
                            ),
                    }
                )

            current = pd.concat(
                [
                    existing,
                    pd.DataFrame(
                        new_rows
                    ),
                ],
                ignore_index=True,
            )

            self.save_results(
                current
            )

        final = self.load_existing()

        completed_after = (
            self.completed_keys(
                final
            )
        )

        print()
        print("-" * 70)

        print(
            f"API calls        : {api_calls}"
        )

        print(
            f"OK               : {success}"
        )

        print(
            f"Sin resultados   : {no_results}"
        )

        print(
            f"Errores          : {errors}"
        )

        print(
            f"Filas acumuladas : {len(final):,}"
        )

        print(
            f"Queries cacheadas: {len(completed_after):,}"
        )

        print()
        print(self.result_path())
        print("=" * 70)

        return self.result_path()
