from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import tldextract


class CompanyCandidateScorer:
    """
    Convierte resultados de búsqueda en empresas únicas.

    Clave principal:
        COMPANY_KEY = SHA1(ROOT_DOMAIN)

    Entrada:
        data/cache/search_results.csv

    Salidas:
        data/cache/company_candidates.csv
        data/cache/companies_master.csv

    companies_master.csv es acumulativo.
    """

    BLOCKED_DOMAINS = {
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "youtube.com",
        "tiktok.com",
        "twitter.com",
        "x.com",
        "wikipedia.org",
        "pinterest.com",
        "reddit.com",
        "mercadolibre.com.pe",
        "mercadolibre.com",
        "computrabajo.com",
        "computrabajo.com.pe",
        "indeed.com",
        "glassdoor.com",
        "bumeran.com.pe",
        "paginasamarillas.com.pe",
        "gob.pe",
        "sunat.gob.pe",
    }

    NICHE_WORDS = {
        "alquiler",
        "leasing",
        "renting",
        "arrendamiento",
        "renta",
        "laptop",
        "laptops",
        "computadora",
        "computadoras",
        "cómputo",
        "tecnológico",
        "tecnologia",
        "tecnología",
        "equipos",
    }

    def __init__(
        self,
        search_results_path="data/cache/search_results.csv",
        cache_root="data/cache",
    ):
        self.search_results_path = Path(search_results_path)
        self.cache_root = Path(cache_root)

    @staticmethod
    def clean(value):
        if pd.isna(value):
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value).strip(),
        )

    @staticmethod
    def company_key(domain):
        return hashlib.sha1(
            str(domain)
            .strip()
            .lower()
            .encode("utf-8")
        ).hexdigest()

    @staticmethod
    def normalize_url(url):
        url = str(url).strip()

        if not url:
            return ""

        if not url.startswith(
            (
                "http://",
                "https://",
            )
        ):
            url = "https://" + url

        return url

    @staticmethod
    def root_domain(url):
        try:
            parsed = urlparse(
                CompanyCandidateScorer.normalize_url(
                    url
                )
            )

            host = (
                parsed.hostname
                or ""
            ).lower()

            host = host.removeprefix(
                "www."
            )

            if not host:
                return ""

            ext = tldextract.extract(
                host
            )

            if ext.domain and ext.suffix:
                return (
                    f"{ext.domain}."
                    f"{ext.suffix}"
                ).lower()

            return host

        except Exception:
            return ""

    @staticmethod
    def candidate_name(title, domain):
        title = str(title).strip()

        if title:
            for separator in [
                " | ",
                " - ",
                " – ",
                " — ",
                " :: ",
            ]:
                if separator in title:
                    title = title.split(
                        separator
                    )[0].strip()

            if 2 <= len(title) <= 120:
                return title

        base = domain.split(".")[0]

        return (
            base
            .replace("-", " ")
            .replace("_", " ")
            .title()
        )

    def excluded_reason(
        self,
        domain,
        url,
    ):
        domain = str(
            domain
        ).lower()

        if not domain:
            return "sin_dominio"

        if domain in self.BLOCKED_DOMAINS:
            return "dominio_bloqueado"

        for blocked in self.BLOCKED_DOMAINS:
            if domain.endswith(
                "." + blocked
            ):
                return "dominio_bloqueado"

        lower_url = str(
            url
        ).lower()

        if lower_url.endswith(
            (
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".zip",
            )
        ):
            return "archivo_no_web"

        return ""

    def score_row(
        self,
        row,
        domain,
    ):
        score = 100

        try:
            position = int(
                float(
                    row.get(
                        "POSITION",
                        99,
                    )
                    or 99
                )
            )
        except Exception:
            position = 99

        if position == 1:
            score += 35
        elif position <= 3:
            score += 25
        elif position <= 5:
            score += 15
        elif position <= 10:
            score += 5

        title = self.clean(
            row.get(
                "TITLE",
                "",
            )
        ).lower()

        snippet = self.clean(
            row.get(
                "SNIPPET",
                "",
            )
        ).lower()

        text = (
            title
            + " "
            + snippet
        )

        matched = sum(
            1
            for word in self.NICHE_WORDS
            if word in text
        )

        score += min(
            matched * 8,
            48,
        )

        if domain.endswith(
            ".com.pe"
        ):
            score += 15

        elif domain.endswith(
            ".pe"
        ):
            score += 10

        elif domain.endswith(
            ".com"
        ):
            score += 5

        if any(
            x in title
            for x in [
                "alquiler",
                "leasing",
                "renting",
                "laptop",
                "computadora",
            ]
        ):
            score += 20

        return score

    def load_results(self):
        if not self.search_results_path.exists():
            raise FileNotFoundError(
                self.search_results_path
            )

        df = pd.read_csv(
            self.search_results_path,
            dtype=str,
            keep_default_na=False,
        )

        required = [
            "STATUS",
            "LINK",
            "TITLE",
            "QUERY",
            "NICHE_ID",
            "PROVIDER",
        ]

        missing = [
            col
            for col in required
            if col not in df.columns
        ]

        if missing:
            raise RuntimeError(
                "Faltan columnas en "
                f"search_results.csv: {missing}"
            )

        df = df[
            df["STATUS"]
            .astype(str)
            .str.upper()
            .eq("OK")
        ].copy()

        df = df[
            df["LINK"]
            .astype(str)
            .str.strip()
            .ne("")
        ].copy()

        return df

    def build_candidates(
        self,
        search_results,
    ):
        rows = []

        for _, row in search_results.iterrows():

            link = self.clean(
                row.get(
                    "LINK",
                    "",
                )
            )

            domain = self.root_domain(
                link
            )

            reason = self.excluded_reason(
                domain,
                link,
            )

            score = self.score_row(
                row,
                domain,
            )

            rows.append(
                {
                    "COMPANY_KEY":
                        self.company_key(
                            domain
                        )
                        if domain
                        else "",
                    "ROOT_DOMAIN":
                        domain,
                    "COMPANY_NAME":
                        self.candidate_name(
                            row.get(
                                "TITLE",
                                "",
                            ),
                            domain,
                        ),
                    "URL":
                        link,
                    "TITLE":
                        self.clean(
                            row.get(
                                "TITLE",
                                "",
                            )
                        ),
                    "SNIPPET":
                        self.clean(
                            row.get(
                                "SNIPPET",
                                "",
                            )
                        ),
                    "NICHE_ID":
                        self.clean(
                            row.get(
                                "NICHE_ID",
                                "",
                            )
                        ),
                    "QUERY":
                        self.clean(
                            row.get(
                                "QUERY",
                                "",
                            )
                        ),
                    "PROVIDER":
                        self.clean(
                            row.get(
                                "PROVIDER",
                                "",
                            )
                        ),
                    "POSITION":
                        self.clean(
                            row.get(
                                "POSITION",
                                "",
                            )
                        ),
                    "CANDIDATE_SCORE":
                        score,
                    "IS_EXCLUDED":
                        "SI"
                        if reason
                        else "NO",
                    "EXCLUDE_REASON":
                        reason,
                }
            )

        return pd.DataFrame(
            rows
        )

    def aggregate_companies(
        self,
        candidates,
    ):
        accepted = candidates[
            candidates[
                "IS_EXCLUDED"
            ] == "NO"
        ].copy()

        if accepted.empty:
            return pd.DataFrame()

        accepted[
            "CANDIDATE_SCORE"
        ] = pd.to_numeric(
            accepted[
                "CANDIDATE_SCORE"
            ],
            errors="coerce",
        ).fillna(0)

        accepted = accepted.sort_values(
            [
                "ROOT_DOMAIN",
                "CANDIDATE_SCORE",
            ],
            ascending=[
                True,
                False,
            ],
        )

        rows = []

        now = datetime.now().isoformat(
            timespec="seconds"
        )

        for (
            company_key,
            domain,
        ), group in accepted.groupby(
            [
                "COMPANY_KEY",
                "ROOT_DOMAIN",
            ],
            dropna=False,
        ):
            group = group.sort_values(
                "CANDIDATE_SCORE",
                ascending=False,
            )

            best = group.iloc[0]

            queries = sorted(
                {
                    x
                    for x in group[
                        "QUERY"
                    ].astype(str)
                    if x.strip()
                }
            )

            niches = sorted(
                {
                    x
                    for x in group[
                        "NICHE_ID"
                    ].astype(str)
                    if x.strip()
                }
            )

            providers = sorted(
                {
                    x
                    for x in group[
                        "PROVIDER"
                    ].astype(str)
                    if x.strip()
                }
            )

            urls = []

            for url in group[
                "URL"
            ].astype(str):
                if (
                    url
                    and url not in urls
                ):
                    urls.append(url)

            rows.append(
                {
                    "COMPANY_KEY":
                        company_key,
                    "ROOT_DOMAIN":
                        domain,
                    "COMPANY_NAME":
                        best[
                            "COMPANY_NAME"
                        ],
                    "BEST_URL":
                        best["URL"],
                    "BEST_SCORE":
                        int(
                            best[
                                "CANDIDATE_SCORE"
                            ]
                        ),
                    "RESULT_COUNT":
                        len(group),
                    "QUERY_COUNT":
                        len(queries),
                    "NICHE_IDS":
                        ";".join(
                            niches
                        ),
                    "PROVIDERS":
                        ";".join(
                            providers
                        ),
                    "QUERIES":
                        ";".join(
                            queries
                        ),
                    "SOURCE_URLS":
                        ";".join(
                            urls[:20]
                        ),
                    "DISCOVERY_STATUS":
                        "DISCOVERED",
                    "DISCOVERED_AT":
                        now,
                    "LAST_SEEN_AT":
                        now,
                }
            )

        return pd.DataFrame(
            rows
        )

    def merge_master(
        self,
        discovered,
    ):
        master_path = (
            self.cache_root
            / "companies_master.csv"
        )

        if not master_path.exists():
            return discovered

        old = pd.read_csv(
            master_path,
            dtype=str,
            keep_default_na=False,
        )

        if old.empty:
            return discovered

        old_map = {
            row["COMPANY_KEY"]:
                row.to_dict()
            for _, row in old.iterrows()
            if str(
                row.get(
                    "COMPANY_KEY",
                    "",
                )
            ).strip()
        }

        merged_rows = []

        current_keys = set()

        for _, row in discovered.iterrows():

            data = row.to_dict()

            key = data[
                "COMPANY_KEY"
            ]

            current_keys.add(
                key
            )

            if key in old_map:
                previous = old_map[
                    key
                ]

                # Preserva columnas futuras:
                # validación, crawl, emails, etc.
                combined = previous.copy()

                old_discovered_at = (
                    previous.get(
                        "DISCOVERED_AT",
                        "",
                    )
                )

                combined.update(
                    data
                )

                if old_discovered_at:
                    combined[
                        "DISCOVERED_AT"
                    ] = old_discovered_at

                merged_rows.append(
                    combined
                )

            else:
                merged_rows.append(
                    data
                )

        # Conserva empresas descubiertas
        # anteriormente aunque no aparezcan
        # en la corrida actual.
        for key, previous in old_map.items():

            if key not in current_keys:
                merged_rows.append(
                    previous
                )

        master = pd.DataFrame(
            merged_rows
        )

        master = master.drop_duplicates(
            subset=[
                "COMPANY_KEY",
            ],
            keep="last",
        )

        return master

    def run(self):
        self.cache_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        results = self.load_results()

        candidates = self.build_candidates(
            results
        )

        discovered = (
            self.aggregate_companies(
                candidates
            )
        )

        master = self.merge_master(
            discovered
        )

        candidates_path = (
            self.cache_root
            / "company_candidates.csv"
        )

        master_path = (
            self.cache_root
            / "companies_master.csv"
        )

        candidates.to_csv(
            candidates_path,
            index=False,
            encoding="utf-8-sig",
        )

        master.to_csv(
            master_path,
            index=False,
            encoding="utf-8-sig",
        )

        excluded = (
            candidates[
                "IS_EXCLUDED"
            ]
            .eq("SI")
            .sum()
            if not candidates.empty
            else 0
        )

        print("=" * 70)
        print(" COMPANY DISCOVERY / DEDUP")
        print("=" * 70)

        print(
            f"Resultados search      : "
            f"{len(results):,}"
        )

        print(
            f"Candidatos analizados  : "
            f"{len(candidates):,}"
        )

        print(
            f"Candidatos excluidos   : "
            f"{excluded:,}"
        )

        print(
            f"Empresas descubiertas  : "
            f"{len(discovered):,}"
        )

        print(
            f"Empresas master total  : "
            f"{len(master):,}"
        )

        print()

        if not master.empty:
            cols = [
                "COMPANY_NAME",
                "ROOT_DOMAIN",
                "BEST_SCORE",
                "RESULT_COUNT",
                "QUERY_COUNT",
                "BEST_URL",
            ]

            print(
                master[
                    cols
                ]
                .sort_values(
                    "BEST_SCORE",
                    ascending=False,
                )
                .head(30)
                .to_string(
                    index=False
                )
            )

        print()
        print(candidates_path)
        print(master_path)
        print("=" * 70)

        return master_path
