from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


class EmailExtractor:

    EMAIL_RE = re.compile(
        r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b",
        re.I,
    )

    MOBILE_RE = re.compile(
        r"(?<!\d)(?:\+?51[\s\-\.]?)?(9\d{8})(?!\d)"
    )

    LIMA_PHONE_RE = re.compile(
        r"(?<!\d)(?:\(01\)|01)?[\s\-\.]?(\d{3})[\s\-\.]?(\d{4})(?!\d)"
    )

    BAD_EMAIL_PARTS = [
        "example.com",
        "email.com",
        "sentry.io",
        "wixpress.com",
        "wordpress.com",
        "cloudflare.com",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
    ]

    def __init__(
        self,
        pages_path="data/cache/crawled_pages.csv",
        emails_path="data/cache/emails_found.csv",
        phones_path="data/cache/phones_found.csv",
        page_log_path="data/cache/contact_extract_page_log.csv",
    ):
        self.pages_path = Path(pages_path)
        self.emails_path = Path(emails_path)
        self.phones_path = Path(phones_path)
        self.page_log_path = Path(page_log_path)

    @staticmethod
    def sha1(value):
        return hashlib.sha1(
            str(value).encode("utf-8")
        ).hexdigest()

    def email_key(self, company_key, email):
        return self.sha1(
            f"{company_key}|{email.lower().strip()}"
        )

    def phone_key(self, company_key, phone):
        return self.sha1(
            f"{company_key}|{phone}"
        )

    @staticmethod
    def load_csv(path, columns=None):
        if not path.exists():
            return pd.DataFrame(
                columns=columns or []
            )

        return pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
        )

    def valid_email(self, email):
        email = (
            str(email)
            .strip()
            .lower()
            .strip(".,;:()[]{}<>\"'")
        )

        if not email:
            return ""

        if any(
            bad in email
            for bad in self.BAD_EMAIL_PARTS
        ):
            return ""

        if ".." in email:
            return ""

        if not self.EMAIL_RE.fullmatch(email):
            return ""

        return email

    def extract_emails(self, html):
        soup = BeautifulSoup(
            html,
            "lxml",
        )

        found = set()

        # mailto suele ser la mejor fuente.
        for tag in soup.find_all(
            "a",
            href=True,
        ):
            href = str(
                tag.get("href", "")
            ).strip()

            if href.lower().startswith(
                "mailto:"
            ):
                value = (
                    href.split(
                        ":",
                        1,
                    )[1]
                    .split("?")[0]
                    .strip()
                )

                for email in self.EMAIL_RE.findall(
                    value
                ):
                    email = self.valid_email(
                        email
                    )

                    if email:
                        found.add(
                            email
                        )

        # También buscamos en el HTML completo.
        for email in self.EMAIL_RE.findall(
            html
        ):
            email = self.valid_email(
                email
            )

            if email:
                found.add(email)

        return sorted(found)

    def extract_phones(self, html):
        soup = BeautifulSoup(
            html,
            "lxml",
        )

        found = set()

        # Prioridad: enlaces tel:
        for tag in soup.find_all(
            "a",
            href=True,
        ):
            href = str(
                tag.get("href", "")
            ).strip()

            if href.lower().startswith(
                "tel:"
            ):
                raw = href.split(
                    ":",
                    1,
                )[1]

                digits = re.sub(
                    r"\D",
                    "",
                    raw,
                )

                if digits.startswith(
                    "51"
                ) and len(digits) > 9:
                    digits = digits[2:]

                if len(digits) in {
                    7,
                    9,
                }:
                    found.add(digits)

        text = soup.get_text(
            " ",
            strip=True,
        )

        for match in self.MOBILE_RE.findall(
            text
        ):
            found.add(match)

        # Lima: 01 + 7 dígitos.
        for match in self.LIMA_PHONE_RE.finditer(
            text
        ):
            phone = (
                match.group(1)
                + match.group(2)
            )

            if len(phone) == 7:
                found.add(phone)

        return sorted(found)

    def run(self):
        if not self.pages_path.exists():
            raise FileNotFoundError(
                self.pages_path
            )

        pages = pd.read_csv(
            self.pages_path,
            dtype=str,
            keep_default_na=False,
        )

        pages = pages[
            pages["CRAWL_STATUS"]
            .astype(str)
            .str.upper()
            .eq("OK")
        ].copy()

        pages = pages[
            pages["HTML_PATH"]
            .astype(str)
            .str.strip()
            .ne("")
        ].copy()

        existing_emails = self.load_csv(
            self.emails_path
        )

        existing_phones = self.load_csv(
            self.phones_path
        )

        page_log = self.load_csv(
            self.page_log_path,
            columns=[
                "PAGE_KEY",
                "COMPANY_KEY",
                "STATUS",
                "EMAILS_FOUND",
                "PHONES_FOUND",
                "PROCESSED_AT",
            ],
        )

        processed_keys = set()

        if not page_log.empty:
            processed_keys = set(
                page_log[
                    page_log["STATUS"].isin(
                        [
                            "PROCESSED",
                            "NO_CONTACTS",
                        ]
                    )
                ]["PAGE_KEY"]
                .astype(str)
            )

        pending = pages[
            ~pages["PAGE_KEY"].isin(
                processed_keys
            )
        ].copy()

        print("=" * 70)
        print(" CONTACT EXTRACTOR - INCREMENTAL")
        print("=" * 70)

        print(
            f"HTML disponibles       : {len(pages):,}"
        )

        print(
            f"HTML ya procesados     : "
            f"{len(pages) - len(pending):,}"
        )

        print(
            f"HTML pendientes        : {len(pending):,}"
        )

        print("-" * 70)

        new_emails = []
        new_phones = []
        new_logs = []

        total = len(pending)

        for number, row in enumerate(
            pending.to_dict("records"),
            start=1,
        ):
            html_path = Path(
                row.get(
                    "HTML_PATH",
                    "",
                )
            )

            print(
                f"[{number}/{total}] "
                f"{row.get('COMPANY_NAME', '')} | "
                f"{row.get('PAGE_URL', '')[:90]}"
            )

            if not html_path.exists():
                new_logs.append(
                    {
                        "PAGE_KEY":
                            row.get(
                                "PAGE_KEY",
                                "",
                            ),
                        "COMPANY_KEY":
                            row.get(
                                "COMPANY_KEY",
                                "",
                            ),
                        "STATUS":
                            "HTML_MISSING",
                        "EMAILS_FOUND":
                            0,
                        "PHONES_FOUND":
                            0,
                        "PROCESSED_AT":
                            datetime.now().isoformat(
                                timespec="seconds"
                            ),
                    }
                )
                continue

            html = html_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            emails = self.extract_emails(
                html
            )

            phones = self.extract_phones(
                html
            )

            company_key = row.get(
                "COMPANY_KEY",
                "",
            )

            for email in emails:
                new_emails.append(
                    {
                        "EMAIL_KEY":
                            self.email_key(
                                company_key,
                                email,
                            ),
                        "COMPANY_KEY":
                            company_key,
                        "COMPANY_NAME":
                            row.get(
                                "COMPANY_NAME",
                                "",
                            ),
                        "ROOT_DOMAIN":
                            row.get(
                                "ROOT_DOMAIN",
                                "",
                            ),
                        "EMAIL":
                            email,
                        "PAGE_KEY":
                            row.get(
                                "PAGE_KEY",
                                "",
                            ),
                        "PAGE_URL":
                            row.get(
                                "PAGE_URL",
                                "",
                            ),
                        "PAGE_TITLE":
                            row.get(
                                "TITLE",
                                "",
                            ),
                        "RENDER_MODE":
                            row.get(
                                "RENDER_MODE",
                                "",
                            ),
                        "HTML_PATH":
                            str(html_path),
                        "FOUND_AT":
                            datetime.now().isoformat(
                                timespec="seconds"
                            ),
                    }
                )

            for phone in phones:
                new_phones.append(
                    {
                        "PHONE_KEY":
                            self.phone_key(
                                company_key,
                                phone,
                            ),
                        "COMPANY_KEY":
                            company_key,
                        "COMPANY_NAME":
                            row.get(
                                "COMPANY_NAME",
                                "",
                            ),
                        "ROOT_DOMAIN":
                            row.get(
                                "ROOT_DOMAIN",
                                "",
                            ),
                        "PHONE":
                            phone,
                        "PAGE_KEY":
                            row.get(
                                "PAGE_KEY",
                                "",
                            ),
                        "PAGE_URL":
                            row.get(
                                "PAGE_URL",
                                "",
                            ),
                        "FOUND_AT":
                            datetime.now().isoformat(
                                timespec="seconds"
                            ),
                    }
                )

            new_logs.append(
                {
                    "PAGE_KEY":
                        row.get(
                            "PAGE_KEY",
                            "",
                        ),
                    "COMPANY_KEY":
                        company_key,
                    "STATUS":
                        (
                            "PROCESSED"
                            if emails or phones
                            else "NO_CONTACTS"
                        ),
                    "EMAILS_FOUND":
                        len(emails),
                    "PHONES_FOUND":
                        len(phones),
                    "PROCESSED_AT":
                        datetime.now().isoformat(
                            timespec="seconds"
                        ),
                }
            )

        emails_final = pd.concat(
            [
                existing_emails,
                pd.DataFrame(new_emails),
            ],
            ignore_index=True,
        )

        if not emails_final.empty:
            emails_final = (
                emails_final
                .drop_duplicates(
                    subset=[
                        "EMAIL_KEY",
                    ],
                    keep="first",
                )
            )

        phones_final = pd.concat(
            [
                existing_phones,
                pd.DataFrame(new_phones),
            ],
            ignore_index=True,
        )

        if not phones_final.empty:
            phones_final = (
                phones_final
                .drop_duplicates(
                    subset=[
                        "PHONE_KEY",
                    ],
                    keep="first",
                )
            )

        log_final = pd.concat(
            [
                page_log,
                pd.DataFrame(new_logs),
            ],
            ignore_index=True,
        )

        if not log_final.empty:
            log_final = (
                log_final
                .drop_duplicates(
                    subset=[
                        "PAGE_KEY",
                    ],
                    keep="last",
                )
            )

        emails_final.to_csv(
            self.emails_path,
            index=False,
            encoding="utf-8-sig",
        )

        phones_final.to_csv(
            self.phones_path,
            index=False,
            encoding="utf-8-sig",
        )

        log_final.to_csv(
            self.page_log_path,
            index=False,
            encoding="utf-8-sig",
        )

        print()
        print("-" * 70)

        print(
            f"Emails nuevos          : {len(new_emails):,}"
        )

        print(
            f"Emails únicos acumulados: {len(emails_final):,}"
        )

        print(
            f"Teléfonos nuevos       : {len(new_phones):,}"
        )

        print(
            f"Teléfonos acumulados   : {len(phones_final):,}"
        )

        if not emails_final.empty:
            print(
                f"Empresas con emails    : "
                f"{emails_final['COMPANY_KEY'].nunique():,}"
            )

        print()
        print(self.emails_path)
        print(self.phones_path)
        print(self.page_log_path)
        print("=" * 70)

        return self.emails_path
