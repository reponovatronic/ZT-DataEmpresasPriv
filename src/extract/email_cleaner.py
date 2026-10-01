from __future__ import annotations

from pathlib import Path

import pandas as pd
import tldextract


class EmailCleaner:

    ROLE_PREFIXES = {
        "ventas": "VENTAS",
        "venta": "VENTAS",
        "sales": "VENTAS",
        "comercial": "COMERCIAL",
        "leasing": "COMERCIAL",
        "renting": "COMERCIAL",
        "alquiler": "COMERCIAL",
        "rentas": "COMERCIAL",

        "contacto": "CONTACTO",
        "contact": "CONTACTO",
        "info": "CONTACTO",
        "informes": "CONTACTO",
        "consulta": "CONTACTO",
        "consultas": "CONTACTO",

        "soporte": "SOPORTE",
        "support": "SOPORTE",
        "servicio": "SOPORTE",
        "servicios": "SOPORTE",
        "help": "SOPORTE",

        "compras": "LOGISTICA",
        "logistica": "LOGISTICA",
        "logística": "LOGISTICA",
        "abastecimiento": "LOGISTICA",
        "proveedores": "LOGISTICA",

        "administracion": "ADMINISTRACION",
        "administración": "ADMINISTRACION",
        "admin": "ADMINISTRACION",
        "facturacion": "ADMINISTRACION",
        "facturación": "ADMINISTRACION",
        "cobranzas": "ADMINISTRACION",

        "marketing": "MARKETING",

        "gerencia": "GERENCIA",
        "gerente": "GERENCIA",

        "rrhh": "RRHH",
        "recursoshumanos": "RRHH",
    }

    # Estos sí los descartamos.
    TECHNICAL_DOMAINS = {
        "example.com",
        "email.com",
        "sentry.io",
        "wixpress.com",
        "cloudflare.com",
    }

    # Estos NO se eliminan.
    # Son correos públicos que una empresa podría publicar.
    GENERIC_EMAIL_DOMAINS = {
        "gmail.com",
        "hotmail.com",
        "outlook.com",
        "yahoo.com",
        "icloud.com",
        "live.com",
    }

    def __init__(
        self,
        emails_path="data/cache/emails_found.csv",
        phones_path="data/cache/phones_found.csv",
        companies_path="data/cache/companies_master.csv",
        output_clean="data/cache/emails_found_clean.csv",
        output_rejected="data/cache/emails_rejected.csv",
        output_summary="data/cache/emails_by_company_clean.csv",
    ):
        self.emails_path = Path(emails_path)
        self.phones_path = Path(phones_path)
        self.companies_path = Path(companies_path)

        self.output_clean = Path(output_clean)
        self.output_rejected = Path(output_rejected)
        self.output_summary = Path(output_summary)

    @staticmethod
    def root_domain(value):
        ext = tldextract.extract(
            str(value)
        )

        if ext.domain and ext.suffix:
            return (
                f"{ext.domain}.{ext.suffix}"
            ).lower()

        return str(value).lower()

    @staticmethod
    def normalize_local(email):
        return (
            email.split("@", 1)[0]
            .lower()
            .replace(".", "")
            .replace("-", "")
            .replace("_", "")
        )

    def classify_area(self, email):
        local = self.normalize_local(
            email
        )

        for prefix, area in self.ROLE_PREFIXES.items():

            normalized = (
                prefix.lower()
                .replace(".", "")
                .replace("-", "")
                .replace("_", "")
            )

            if (
                local == normalized
                or local.startswith(normalized)
            ):
                return (
                    "ROL_INSTITUCIONAL",
                    area,
                )

        return (
            "PERSONAL_PUBLICO",
            "GENERAL",
        )

    def classify_domain(
        self,
        email_domain,
        official_domain,
    ):
        email_root = self.root_domain(
            email_domain
        )

        official_root = self.root_domain(
            official_domain
        )

        if email_root in self.TECHNICAL_DOMAINS:
            return "TECNICO"

        if email_root == official_root:
            return "DOMINIO_OFICIAL"

        if email_root in self.GENERIC_EMAIL_DOMAINS:
            return "PUBLICO_GENERICO"

        return "DOMINIO_EXTERNO_PUBLICADO"

    @staticmethod
    def priority(
        email_type,
        area,
        domain_status,
    ):
        domain_score = {
            "DOMINIO_OFICIAL": 500,
            "DOMINIO_EXTERNO_PUBLICADO": 300,
            "PUBLICO_GENERICO": 200,
        }.get(
            domain_status,
            0,
        )

        type_score = (
            150
            if email_type == "ROL_INSTITUCIONAL"
            else 50
        )

        area_score = {
            "VENTAS": 100,
            "CONTACTO": 95,
            "COMERCIAL": 90,
            "SOPORTE": 85,
            "LOGISTICA": 80,
            "GERENCIA": 70,
            "ADMINISTRACION": 60,
            "MARKETING": 40,
            "RRHH": 20,
            "GENERAL": 0,
        }.get(
            area,
            0,
        )

        return (
            domain_score
            + type_score
            + area_score
        )

    def run(self):

        if not self.emails_path.exists():
            raise FileNotFoundError(
                self.emails_path
            )

        emails = pd.read_csv(
            self.emails_path,
            dtype=str,
            keep_default_na=False,
        )

        companies = pd.read_csv(
            self.companies_path,
            dtype=str,
            keep_default_na=False,
        )

        phones = pd.DataFrame()

        if self.phones_path.exists():
            phones = pd.read_csv(
                self.phones_path,
                dtype=str,
                keep_default_na=False,
            )

        domain_map = dict(
            zip(
                companies["COMPANY_KEY"],
                companies["ROOT_DOMAIN"],
            )
        )

        accepted = []
        rejected = []

        for _, row in emails.iterrows():

            data = row.to_dict()

            email = (
                data.get(
                    "EMAIL",
                    "",
                )
                .strip()
                .lower()
            )

            if "@" not in email:
                continue

            company_key = data.get(
                "COMPANY_KEY",
                "",
            )

            official_domain = (
                domain_map.get(
                    company_key,
                    data.get(
                        "ROOT_DOMAIN",
                        "",
                    ),
                )
                .lower()
            )

            email_domain = email.split(
                "@",
                1,
            )[1]

            domain_status = (
                self.classify_domain(
                    email_domain,
                    official_domain,
                )
            )

            data["EMAIL_DOMAIN"] = (
                email_domain
            )

            data["EMAIL_DOMAIN_STATUS"] = (
                domain_status
            )

            if domain_status == "TECNICO":

                data["CLEAN_STATUS"] = (
                    "REJECT"
                )

                data["CLEAN_REASON"] = (
                    "dominio_tecnico"
                )

                rejected.append(
                    data
                )

                continue

            email_type, area = (
                self.classify_area(
                    email
                )
            )

            score = self.priority(
                email_type,
                area,
                domain_status,
            )

            data["EMAIL_TYPE"] = (
                email_type
            )

            data["EMAIL_AREA"] = (
                area
            )

            data[
                "EMAIL_PRIORITY_SCORE"
            ] = score

            data["CLEAN_STATUS"] = (
                "ACCEPT"
            )

            data["CLEAN_REASON"] = (
                "correo_publicado_en_web_empresa"
            )

            accepted.append(
                data
            )

        clean = pd.DataFrame(
            accepted
        )

        rejected_df = pd.DataFrame(
            rejected
        )

        if not clean.empty:
            clean[
                "EMAIL_PRIORITY_SCORE"
            ] = pd.to_numeric(
                clean[
                    "EMAIL_PRIORITY_SCORE"
                ],
                errors="coerce",
            ).fillna(0)

            clean = clean.sort_values(
                [
                    "COMPANY_KEY",
                    "EMAIL_PRIORITY_SCORE",
                ],
                ascending=[
                    True,
                    False,
                ],
            )

        summary_rows = []

        for _, company in companies.iterrows():

            company_key = company[
                "COMPANY_KEY"
            ]

            if clean.empty:
                group = pd.DataFrame()

            else:
                group = clean[
                    clean[
                        "COMPANY_KEY"
                    ] == company_key
                ].copy()

            def area_emails(area):

                if group.empty:
                    return ""

                values = (
                    group[
                        group[
                            "EMAIL_AREA"
                        ] == area
                    ]["EMAIL"]
                    .drop_duplicates()
                    .tolist()
                )

                return ";".join(
                    values
                )

            all_emails = (
                group[
                    "EMAIL"
                ]
                .drop_duplicates()
                .tolist()
                if not group.empty
                else []
            )

            official = (
                group[
                    group[
                        "EMAIL_DOMAIN_STATUS"
                    ] == "DOMINIO_OFICIAL"
                ]["EMAIL"]
                .drop_duplicates()
                .tolist()
                if not group.empty
                else []
            )

            generic = (
                group[
                    group[
                        "EMAIL_DOMAIN_STATUS"
                    ] == "PUBLICO_GENERICO"
                ]["EMAIL"]
                .drop_duplicates()
                .tolist()
                if not group.empty
                else []
            )

            external = (
                group[
                    group[
                        "EMAIL_DOMAIN_STATUS"
                    ]
                    == "DOMINIO_EXTERNO_PUBLICADO"
                ]["EMAIL"]
                .drop_duplicates()
                .tolist()
                if not group.empty
                else []
            )

            role = (
                group[
                    group[
                        "EMAIL_TYPE"
                    ] == "ROL_INSTITUCIONAL"
                ]["EMAIL"]
                .drop_duplicates()
                .tolist()
                if not group.empty
                else []
            )

            personal = (
                group[
                    group[
                        "EMAIL_TYPE"
                    ] == "PERSONAL_PUBLICO"
                ]["EMAIL"]
                .drop_duplicates()
                .tolist()
                if not group.empty
                else []
            )

            principal = (
                group.iloc[0]["EMAIL"]
                if not group.empty
                else ""
            )

            if official:
                estado = (
                    "CON_CORREO_OFICIAL"
                )

            elif generic:
                estado = (
                    "CON_CORREO_PUBLICO_GENERICO"
                )

            elif external:
                estado = (
                    "CON_CORREO_EXTERNO_PUBLICADO"
                )

            else:
                estado = "SIN_EMAIL"

            phone_list = []

            if not phones.empty:
                phone_list = (
                    phones[
                        phones[
                            "COMPANY_KEY"
                        ] == company_key
                    ]["PHONE"]
                    .drop_duplicates()
                    .tolist()
                )

            summary_rows.append(
                {
                    "COMPANY_KEY":
                        company_key,

                    "ESTADO_EMAIL":
                        estado,

                    "EMAIL_PRINCIPAL":
                        principal,

                    "EMAIL_VENTAS":
                        area_emails(
                            "VENTAS"
                        ),

                    "EMAIL_CONTACTO":
                        area_emails(
                            "CONTACTO"
                        ),

                    "EMAIL_COMERCIAL":
                        area_emails(
                            "COMERCIAL"
                        ),

                    "EMAIL_SOPORTE":
                        area_emails(
                            "SOPORTE"
                        ),

                    "EMAIL_LOGISTICA":
                        area_emails(
                            "LOGISTICA"
                        ),

                    "EMAIL_ADMINISTRACION":
                        area_emails(
                            "ADMINISTRACION"
                        ),

                    "EMAIL_GERENCIA":
                        area_emails(
                            "GERENCIA"
                        ),

                    "EMAILS_DOMINIO_OFICIAL":
                        ";".join(
                            official
                        ),

                    "EMAILS_PUBLICOS_GENERICOS":
                        ";".join(
                            generic
                        ),

                    "EMAILS_EXTERNOS_PUBLICADOS":
                        ";".join(
                            external
                        ),

                    "EMAILS_ROL_INSTITUCIONAL":
                        ";".join(
                            role
                        ),

                    "EMAILS_PERSONALES_PUBLICOS":
                        ";".join(
                            personal
                        ),

                    "EMAILS_TODOS":
                        ";".join(
                            all_emails
                        ),

                    "TOTAL_EMAILS":
                        len(
                            all_emails
                        ),

                    "TOTAL_ROL_INSTITUCIONAL":
                        len(
                            role
                        ),

                    "TOTAL_PERSONALES_PUBLICOS":
                        len(
                            personal
                        ),

                    "TELEFONOS":
                        ";".join(
                            phone_list
                        ),
                }
            )

        summary = pd.DataFrame(
            summary_rows
        )

        clean.to_csv(
            self.output_clean,
            index=False,
            encoding="utf-8-sig",
        )

        rejected_df.to_csv(
            self.output_rejected,
            index=False,
            encoding="utf-8-sig",
        )

        summary.to_csv(
            self.output_summary,
            index=False,
            encoding="utf-8-sig",
        )

        print("=" * 70)
        print(" EMAIL CLEANER V2")
        print("=" * 70)

        print(
            f"Emails originales       : {len(emails):,}"
        )

        print(
            f"Emails aceptados        : {len(clean):,}"
        )

        print(
            f"Emails rechazados       : {len(rejected_df):,}"
        )

        print(
            f"Empresas master         : {len(companies):,}"
        )

        print(
            f"Empresas con email      : "
            f"{summary['ESTADO_EMAIL'].ne('SIN_EMAIL').sum():,}"
        )

        print()

        if not clean.empty:
            print(
                clean[
                    [
                        "COMPANY_NAME",
                        "EMAIL",
                        "EMAIL_DOMAIN_STATUS",
                        "EMAIL_TYPE",
                        "EMAIL_AREA",
                        "EMAIL_PRIORITY_SCORE",
                    ]
                ]
                .head(50)
                .to_string(
                    index=False
                )
            )

        print()
        print(self.output_clean)
        print(self.output_rejected)
        print(self.output_summary)
        print("=" * 70)

        return self.output_summary
