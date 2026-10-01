from __future__ import annotations

from pathlib import Path
from urllib.parse import (
    parse_qsl,
    urlencode,
    urlparse,
    urlunparse,
)

import pandas as pd
import tldextract


class CrawlSeedBuilder:

    def __init__(
        self,
        validated_path="data/cache/web_validated.csv",
        companies_path="data/cache/companies_master.csv",
        output_path="data/cache/crawl_seeds.csv",
    ):
        self.validated_path = Path(validated_path)
        self.companies_path = Path(companies_path)
        self.output_path = Path(output_path)

    @staticmethod
    def normalize_url(url):
        url = str(url).strip()

        if not url:
            return ""

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)

        clean_query = []

        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        ):
            key_lower = key.lower()

            if (
                key_lower.startswith("utm_")
                or key_lower in {
                    "srsltid",
                    "gclid",
                    "fbclid",
                }
            ):
                continue

            clean_query.append(
                (key, value)
            )

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path or "/",
                "",
                urlencode(clean_query),
                "",
            )
        )

    @staticmethod
    def root_domain(url):
        ext = tldextract.extract(url)

        if ext.domain and ext.suffix:
            return (
                f"{ext.domain}.{ext.suffix}"
            ).lower()

        return ""

    @staticmethod
    def home_url(url):
        parsed = urlparse(url)

        return (
            f"{parsed.scheme}://"
            f"{parsed.netloc}/"
        )

    def run(self):
        if not self.validated_path.exists():
            raise FileNotFoundError(
                self.validated_path
            )

        validated = pd.read_csv(
            self.validated_path,
            dtype=str,
            keep_default_na=False,
        )

        validated = validated[
            validated[
                "VALIDATION_STATUS"
            ].astype(str).str.upper().eq("OK")
        ].copy()

        companies = pd.DataFrame()

        if self.companies_path.exists():
            companies = pd.read_csv(
                self.companies_path,
                dtype=str,
                keep_default_na=False,
            )

        rows = []

        for _, row in validated.iterrows():

            company_key = row.get(
                "COMPANY_KEY",
                "",
            )

            company_name = row.get(
                "COMPANY_NAME",
                "",
            )

            domain = row.get(
                "ROOT_DOMAIN",
                "",
            )

            final_url = self.normalize_url(
                row.get(
                    "FINAL_URL",
                    "",
                )
            )

            if not final_url:
                continue

            candidates = [
                (
                    "WEB_VALIDATED",
                    999,
                    final_url,
                ),
                (
                    "HOME",
                    950,
                    self.normalize_url(
                        self.home_url(
                            final_url
                        )
                    ),
                ),
            ]

            # También aprovechamos URLs encontradas
            # por los buscadores para esa empresa.
            if not companies.empty:

                match = companies[
                    companies[
                        "COMPANY_KEY"
                    ] == company_key
                ]

                if not match.empty:

                    source_urls = (
                        match.iloc[0]
                        .get(
                            "SOURCE_URLS",
                            "",
                        )
                    )

                    for source_url in str(
                        source_urls
                    ).split(";"):

                        source_url = (
                            self.normalize_url(
                                source_url
                            )
                        )

                        if not source_url:
                            continue

                        if (
                            self.root_domain(
                                source_url
                            )
                            != domain
                        ):
                            continue

                        candidates.append(
                            (
                                "SEARCH_RESULT",
                                800,
                                source_url,
                            )
                        )

            seen = set()

            for (
                seed_type,
                score,
                seed_url,
            ) in candidates:

                if not seed_url:
                    continue

                if seed_url in seen:
                    continue

                seen.add(seed_url)

                rows.append(
                    {
                        "COMPANY_KEY":
                            company_key,
                        "COMPANY_NAME":
                            company_name,
                        "ROOT_DOMAIN":
                            domain,
                        "SEED_TYPE":
                            seed_type,
                        "SEED_SCORE":
                            score,
                        "SEED_URL":
                            seed_url,
                    }
                )

        df = pd.DataFrame(
            rows
        )

        if not df.empty:
            df = df.drop_duplicates(
                subset=[
                    "COMPANY_KEY",
                    "SEED_URL",
                ],
                keep="first",
            )

            df = df.sort_values(
                [
                    "COMPANY_KEY",
                    "SEED_SCORE",
                ],
                ascending=[
                    True,
                    False,
                ],
            )

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        df.to_csv(
            self.output_path,
            index=False,
            encoding="utf-8-sig",
        )

        print("=" * 70)
        print(" CRAWL SEED BUILDER")
        print("=" * 70)

        print(
            f"Empresas validadas : "
            f"{validated['COMPANY_KEY'].nunique():,}"
        )

        print(
            f"Seeds generadas     : "
            f"{len(df):,}"
        )

        print()

        if not df.empty:
            print(
                df[
                    [
                        "COMPANY_NAME",
                        "ROOT_DOMAIN",
                        "SEED_TYPE",
                        "SEED_SCORE",
                        "SEED_URL",
                    ]
                ]
                .head(40)
                .to_string(index=False)
            )

        print()
        print(self.output_path)
        print("=" * 70)

        return self.output_path
