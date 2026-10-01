from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


class WebValidator:

    def __init__(
        self,
        companies_path="data/cache/companies_master.csv",
        output_path="data/cache/web_validated.csv",
        timeout=20,
    ):
        self.companies_path = Path(companies_path)
        self.output_path = Path(output_path)
        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                )
            }
        )

    @staticmethod
    def validation_key(
        company_key,
        url,
    ):
        raw = (
            f"{company_key}|"
            f"{str(url).strip().lower()}"
        )

        return hashlib.sha1(
            raw.encode("utf-8")
        ).hexdigest()

    def load_companies(self):
        if not self.companies_path.exists():
            raise FileNotFoundError(
                self.companies_path
            )

        return pd.read_csv(
            self.companies_path,
            dtype=str,
            keep_default_na=False,
        )

    def load_existing(self):
        columns = [
            "VALIDATION_KEY",
            "COMPANY_KEY",
            "COMPANY_NAME",
            "ROOT_DOMAIN",
            "ORIGINAL_URL",
            "FINAL_URL",
            "HTTP_STATUS",
            "CONTENT_TYPE",
            "VALIDATION_STATUS",
            "ERROR",
            "VALIDATED_AT",
        ]

        if not self.output_path.exists():
            return pd.DataFrame(
                columns=columns
            )

        df = pd.read_csv(
            self.output_path,
            dtype=str,
            keep_default_na=False,
        )

        for col in columns:
            if col not in df.columns:
                df[col] = ""

        return df

    def validate(self, url):
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
            )

            content_type = (
                response.headers.get(
                    "Content-Type",
                    "",
                )
            )

            if response.status_code < 400:
                status = "OK"
            else:
                status = "ERROR"

            return {
                "FINAL_URL":
                    response.url,
                "HTTP_STATUS":
                    response.status_code,
                "CONTENT_TYPE":
                    content_type,
                "VALIDATION_STATUS":
                    status,
                "ERROR":
                    "",
            }

        except Exception as exc:
            return {
                "FINAL_URL":
                    "",
                "HTTP_STATUS":
                    "",
                "CONTENT_TYPE":
                    "",
                "VALIDATION_STATUS":
                    "ERROR",
                "ERROR":
                    str(exc),
            }

    def run(self):
        companies = self.load_companies()

        existing = self.load_existing()

        cache_keys = set()

        if not existing.empty:
            cached = existing[
                existing[
                    "VALIDATION_STATUS"
                ].astype(str).str.upper().eq("OK")
            ]

            cache_keys = set(
                cached[
                    "VALIDATION_KEY"
                ].astype(str)
            )

        rows = []

        pending = []

        for _, company in companies.iterrows():

            company_key = company.get(
                "COMPANY_KEY",
                "",
            )

            best_url = company.get(
                "BEST_URL",
                "",
            )

            key = self.validation_key(
                company_key,
                best_url,
            )

            if key in cache_keys:
                continue

            pending.append(
                (
                    company,
                    key,
                )
            )

        print("=" * 70)
        print(" WEB VALIDATOR - INCREMENTAL")
        print("=" * 70)

        print(
            f"Empresas master     : {len(companies):,}"
        )

        print(
            f"Webs en cache       : "
            f"{len(companies) - len(pending):,}"
        )

        print(
            f"Webs pendientes     : {len(pending):,}"
        )

        print("-" * 70)

        for number, (
            company,
            key,
        ) in enumerate(
            pending,
            start=1,
        ):
            name = company.get(
                "COMPANY_NAME",
                "",
            )

            url = company.get(
                "BEST_URL",
                "",
            )

            print(
                f"[{number}/{len(pending)}] "
                f"{name} | {url}"
            )

            result = self.validate(
                url
            )

            rows.append(
                {
                    "VALIDATION_KEY":
                        key,
                    "COMPANY_KEY":
                        company.get(
                            "COMPANY_KEY",
                            "",
                        ),
                    "COMPANY_NAME":
                        name,
                    "ROOT_DOMAIN":
                        company.get(
                            "ROOT_DOMAIN",
                            "",
                        ),
                    "ORIGINAL_URL":
                        url,
                    "FINAL_URL":
                        result[
                            "FINAL_URL"
                        ],
                    "HTTP_STATUS":
                        result[
                            "HTTP_STATUS"
                        ],
                    "CONTENT_TYPE":
                        result[
                            "CONTENT_TYPE"
                        ],
                    "VALIDATION_STATUS":
                        result[
                            "VALIDATION_STATUS"
                        ],
                    "ERROR":
                        result[
                            "ERROR"
                        ],
                    "VALIDATED_AT":
                        datetime.now()
                        .isoformat(
                            timespec="seconds"
                        ),
                }
            )

            current = pd.concat(
                [
                    existing,
                    pd.DataFrame(rows),
                ],
                ignore_index=True,
            )

            current = current.drop_duplicates(
                subset=[
                    "VALIDATION_KEY",
                ],
                keep="last",
            )

            current.to_csv(
                self.output_path,
                index=False,
                encoding="utf-8-sig",
            )

        final = self.load_existing()

        print()
        print("-" * 70)

        print(
            f"Webs validadas total : {len(final):,}"
        )

        if not final.empty:
            print(
                f"OK                  : "
                f"{final['VALIDATION_STATUS'].eq('OK').sum():,}"
            )

            print(
                f"ERROR               : "
                f"{final['VALIDATION_STATUS'].eq('ERROR').sum():,}"
            )

        print()
        print(self.output_path)
        print("=" * 70)

        return self.output_path
