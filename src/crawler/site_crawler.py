from __future__ import annotations

import hashlib
import re
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.parse import (
    parse_qsl,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

import pandas as pd
import requests
import tldextract
from bs4 import BeautifulSoup

from src.crawler.js_renderer import JSRenderer


class SiteCrawler:

    # =========================================================
    # PRIORIDADES DE NAVEGACIÓN
    # =========================================================

    # Máxima prioridad.
    # Nuestro objetivo comercial es encontrar formas de contacto.
    CONTACT_PRIORITY_WORDS = [
        "contacto",
        "contact",
        "contactanos",
        "contáctanos",
        "contact-us",
        "contactus",
        "ventas",
        "venta",
        "sales",
        "comercial",
        "comerciales",
        "cotiza",
        "cotizar",
        "cotizacion",
        "cotización",
        "presupuesto",
        "asesor",
        "asesores",
        "ejecutivo",
        "ejecutivos",
        "soporte",
        "support",
        "servicio-tecnico",
        "servicio técnico",
        "atencion",
        "atención",
        "whatsapp",
        "llamanos",
        "llámanos",
        "escribenos",
        "escríbenos",
    ]

    # Segunda prioridad.
    PRIORITY_WORDS = [
        "nosotros",
        "empresa",
        "about",
        "quienes-somos",
        "quiénes somos",
        "quienes somos",
        "equipo",
        "team",
        "staff",
        "directorio",
        "leasing",
        "renting",
        "alquiler",
        "arrendamiento",
        "servicio",
        "servicios",
        "soluciones",
        "clientes",
    ]

    # Evitar páginas que normalmente no aportan contactos.
    SKIP_WORDS = [
        "login",
        "signin",
        "registro",
        "register",
        "carrito",
        "cart",
        "checkout",
        "privacy",
        "privacidad",
        "cookies",
        "terminos",
        "términos",
        "terms",
        "politica",
        "política",
        "wishlist",
        "favoritos",
        "mi-cuenta",
        "my-account",
    ]

    # Si desde la home no encontramos suficientes enlaces de
    # contacto, probamos rutas frecuentes.
    COMMON_CONTACT_PATHS = [
        "/contacto",
        "/contacto/",
        "/contact",
        "/contact/",
        "/contactanos",
        "/contactanos/",
        "/contact-us",
        "/ventas",
        "/ventas/",
        "/comercial",
        "/comercial/",
        "/cotiza",
        "/cotiza/",
        "/cotizar",
        "/cotizar/",
        "/soporte",
        "/soporte/",
        "/servicio-tecnico",
        "/servicio-tecnico/",
        "/nosotros",
        "/nosotros/",
        "/quienes-somos",
        "/quienes-somos/",
        "/empresa",
        "/empresa/",
    ]

    BINARY_EXTENSIONS = (
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".zip",
        ".rar",
        ".7z",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".mp4",
        ".mp3",
        ".avi",
        ".mov",
    )

    def __init__(
        self,
        seeds_path="data/cache/crawl_seeds.csv",
        output_path="data/cache/crawled_pages.csv",
        seed_log_path="data/cache/crawl_seed_log.csv",
        html_root="data/cache/html",
        timeout=20,
        delay_seconds=0.35,
        enable_js=True,
    ):
        self.seeds_path = Path(
            seeds_path
        )

        self.output_path = Path(
            output_path
        )

        self.seed_log_path = Path(
            seed_log_path
        )

        self.html_root = Path(
            html_root
        )

        self.timeout = timeout
        self.delay_seconds = (
            delay_seconds
        )

        self.enable_js = enable_js

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "*/*;q=0.8"
                ),
                "Accept-Language":
                    "es-PE,es;q=0.9,en;q=0.8",
            }
        )

        self.renderer = (
            JSRenderer()
            if enable_js
            else None
        )

    # =========================================================
    # HASH / URL
    # =========================================================

    @staticmethod
    def sha1(value):
        return hashlib.sha1(
            str(value)
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
            url = (
                "https://"
                + url
            )

        try:
            parsed = urlparse(
                url
            )

            query = []

            for key, value in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            ):
                key_lower = (
                    key.lower()
                )

                if (
                    key_lower.startswith(
                        "utm_"
                    )
                    or key_lower
                    in {
                        "srsltid",
                        "gclid",
                        "fbclid",
                        "msclkid",
                    }
                ):
                    continue

                query.append(
                    (
                        key,
                        value,
                    )
                )

            path = re.sub(
                r"/+",
                "/",
                parsed.path or "/",
            )

            return urlunparse(
                (
                    parsed.scheme.lower(),
                    parsed.netloc.lower(),
                    path,
                    "",
                    urlencode(
                        query
                    ),
                    "",
                )
            )

        except Exception:
            return ""

    @staticmethod
    def root_domain(url):

        try:
            ext = (
                tldextract.extract(
                    url
                )
            )

            if (
                ext.domain
                and ext.suffix
            ):
                return (
                    f"{ext.domain}."
                    f"{ext.suffix}"
                ).lower()

        except Exception:
            pass

        return ""

    @staticmethod
    def home_url(url):

        try:
            parsed = urlparse(
                url
            )

            return (
                f"{parsed.scheme}://"
                f"{parsed.netloc}/"
            )

        except Exception:
            return ""

    def seed_key(
        self,
        company_key,
        seed_url,
    ):
        return self.sha1(
            f"{company_key}|"
            f"{self.normalize_url(seed_url)}"
        )

    def page_key(
        self,
        company_key,
        page_url,
    ):
        return self.sha1(
            f"{company_key}|"
            f"{self.normalize_url(page_url)}"
        )

    # =========================================================
    # LOAD
    # =========================================================

    def load_seeds(
        self,
        limit_companies=None,
    ):

        if not self.seeds_path.exists():
            raise FileNotFoundError(
                self.seeds_path
            )

        df = pd.read_csv(
            self.seeds_path,
            dtype=str,
            keep_default_na=False,
        )

        if limit_companies is not None:

            company_keys = (
                df["COMPANY_KEY"]
                .drop_duplicates()
                .head(
                    limit_companies
                )
                .tolist()
            )

            df = df[
                df[
                    "COMPANY_KEY"
                ].isin(
                    company_keys
                )
            ].copy()

        df["SEED_KEY"] = df.apply(
            lambda r: self.seed_key(
                r.get(
                    "COMPANY_KEY",
                    "",
                ),
                r.get(
                    "SEED_URL",
                    "",
                ),
            ),
            axis=1,
        )

        return df

    def load_pages(self):

        columns = [
            "PAGE_KEY",
            "SEED_KEY",
            "COMPANY_KEY",
            "COMPANY_NAME",
            "ROOT_DOMAIN",
            "SEED_TYPE",
            "SEED_URL",
            "PAGE_URL",
            "FINAL_URL",
            "HTTP_STATUS",
            "CONTENT_TYPE",
            "TITLE",
            "RENDER_MODE",
            "NEEDS_JS",
            "VISIBLE_TEXT_LENGTH",
            "LINKS_FOUND",
            "CONTACT_LINKS_FOUND",
            "HTML_PATH",
            "CRAWL_STATUS",
            "ERROR",
            "CRAWLED_AT",
        ]

        if not self.output_path.exists():
            return pd.DataFrame(
                columns=columns
            )

        try:
            df = pd.read_csv(
                self.output_path,
                dtype=str,
                keep_default_na=False,
            )

        except pd.errors.EmptyDataError:
            return pd.DataFrame(
                columns=columns
            )

        for col in columns:
            if col not in df.columns:
                df[col] = ""

        return df

    def load_seed_log(self):

        columns = [
            "SEED_KEY",
            "COMPANY_KEY",
            "COMPANY_NAME",
            "ROOT_DOMAIN",
            "SEED_TYPE",
            "SEED_URL",
            "STATUS",
            "PAGES_NEW",
            "PROCESSED_AT",
        ]

        if not self.seed_log_path.exists():
            return pd.DataFrame(
                columns=columns
            )

        try:
            df = pd.read_csv(
                self.seed_log_path,
                dtype=str,
                keep_default_na=False,
            )

        except pd.errors.EmptyDataError:
            return pd.DataFrame(
                columns=columns
            )

        for col in columns:
            if col not in df.columns:
                df[col] = ""

        return df

    # =========================================================
    # HTML / JS
    # =========================================================

    @staticmethod
    def visible_text_length(
        html,
    ):

        if not html:
            return 0

        try:
            soup = BeautifulSoup(
                html,
                "lxml",
            )

            for tag in soup(
                [
                    "script",
                    "style",
                    "noscript",
                    "svg",
                ]
            ):
                tag.decompose()

            text = soup.get_text(
                " ",
                strip=True,
            )

            return len(text)

        except Exception:
            return 0

    @staticmethod
    def title_from_html(
        html,
    ):

        if not html:
            return ""

        try:
            soup = BeautifulSoup(
                html,
                "lxml",
            )

            if soup.title:
                return (
                    soup.title
                    .get_text(
                        " ",
                        strip=True,
                    )
                )

        except Exception:
            pass

        return ""

    def detect_js(
        self,
        html,
        visible_length,
    ):

        lower = str(
            html
        ).lower()

        indicators = [
            'id="root"',
            "id='root'",
            'id="app"',
            "id='app'",
            "__next_data__",
            "_next/static",
            "__nuxt",
            "_nuxt/",
            "vite",
            "webpack",
            "react",
            "react-dom",
            "ng-version",
            "angular",
            "vue",
            "vue.js",
        ]

        indicator_found = any(
            x in lower
            for x in indicators
        )

        # Prácticamente no hay contenido visible.
        if visible_length < 250:
            return True

        # Página parece SPA pero requests trae poco contenido.
        if (
            visible_length < 700
            and indicator_found
        ):
            return True

        return False

    # =========================================================
    # REQUESTS
    # =========================================================

    def fetch_requests(
        self,
        url,
    ):

        try:
            response = (
                self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
            )

            content_type = (
                response.headers.get(
                    "Content-Type",
                    "",
                )
            )

            # No queremos guardar binarios como HTML.
            if (
                content_type
                and "text/html"
                not in content_type.lower()
                and "application/xhtml"
                not in content_type.lower()
            ):
                return {
                    "STATUS":
                        "ERROR",
                    "HTTP_STATUS":
                        response.status_code,
                    "FINAL_URL":
                        response.url,
                    "CONTENT_TYPE":
                        content_type,
                    "TITLE":
                        "",
                    "HTML":
                        "",
                    "VISIBLE_TEXT_LENGTH":
                        0,
                    "NEEDS_JS":
                        False,
                    "ERROR":
                        "contenido_no_html",
                }

            html = (
                response.text
                or ""
            )

            visible_length = (
                self.visible_text_length(
                    html
                )
            )

            needs_js = (
                self.detect_js(
                    html,
                    visible_length,
                )
            )

            return {
                "STATUS":
                    (
                        "OK"
                        if response.status_code
                        < 400
                        else "ERROR"
                    ),
                "HTTP_STATUS":
                    response.status_code,
                "FINAL_URL":
                    response.url,
                "CONTENT_TYPE":
                    content_type,
                "TITLE":
                    self.title_from_html(
                        html
                    ),
                "HTML":
                    html,
                "VISIBLE_TEXT_LENGTH":
                    visible_length,
                "NEEDS_JS":
                    needs_js,
                "ERROR":
                    "",
            }

        except Exception as exc:

            return {
                "STATUS":
                    "ERROR",
                "HTTP_STATUS":
                    "",
                "FINAL_URL":
                    "",
                "CONTENT_TYPE":
                    "",
                "TITLE":
                    "",
                "HTML":
                    "",
                "VISIBLE_TEXT_LENGTH":
                    0,
                "NEEDS_JS":
                    True,
                "ERROR":
                    str(exc),
            }

    # =========================================================
    # REQUESTS + PLAYWRIGHT
    # =========================================================

    def fetch_page(
        self,
        url,
    ):

        request_result = (
            self.fetch_requests(
                url
            )
        )

        should_render = (
            self.enable_js
            and self.renderer is not None
            and (
                request_result.get(
                    "NEEDS_JS",
                    False,
                )
                or (
                    request_result.get(
                        "STATUS"
                    )
                    == "ERROR"
                    and str(
                        request_result.get(
                            "HTTP_STATUS",
                            "",
                        )
                    )
                    in {
                        "401",
                        "403",
                        "429",
                    }
                )
            )
        )

        if should_render:

            rendered = (
                self.renderer.render(
                    url
                )
            )

            if (
                rendered.get(
                    "STATUS"
                )
                == "OK"
                and rendered.get(
                    "HTML"
                )
            ):
                html = rendered[
                    "HTML"
                ]

                visible_length = (
                    self.visible_text_length(
                        html
                    )
                )

                return {
                    "STATUS":
                        "OK",
                    "HTTP_STATUS":
                        rendered.get(
                            "HTTP_STATUS",
                            "",
                        ),
                    "FINAL_URL":
                        rendered.get(
                            "FINAL_URL",
                            url,
                        ),
                    "CONTENT_TYPE":
                        (
                            "text/html; "
                            "rendered=playwright"
                        ),
                    "TITLE":
                        rendered.get(
                            "TITLE",
                            "",
                        ),
                    "HTML":
                        html,
                    "VISIBLE_TEXT_LENGTH":
                        visible_length,
                    "NEEDS_JS":
                        True,
                    "RENDER_MODE":
                        "playwright",
                    "ERROR":
                        "",
                }

        request_result[
            "RENDER_MODE"
        ] = "requests"

        return request_result

    # =========================================================
    # LINK SCORING
    # =========================================================

    def link_score(
        self,
        url,
        text,
    ):

        value = (
            str(url)
            + " "
            + str(text)
        ).lower()

        score = 0

        # Máxima prioridad.
        for word in (
            self.CONTACT_PRIORITY_WORDS
        ):
            if word in value:
                score += 150

        # Prioridad media.
        for word in (
            self.PRIORITY_WORDS
        ):
            if word in value:
                score += 40

        # Evitar páginas irrelevantes.
        for word in (
            self.SKIP_WORDS
        ):
            if word in value:
                score -= 250

        # La home tiene cierta utilidad.
        parsed = urlparse(
            str(url)
        )

        if (
            parsed.path
            in {
                "",
                "/",
            }
        ):
            score += 20

        return score

    def is_contact_link(
        self,
        url,
        text="",
    ):

        value = (
            str(url)
            + " "
            + str(text)
        ).lower()

        return any(
            word in value
            for word
            in self.CONTACT_PRIORITY_WORDS
        )

    # =========================================================
    # EXTRACCIÓN DE LINKS
    # =========================================================

    def extract_internal_links(
        self,
        html,
        base_url,
        root_domain,
    ):

        try:
            soup = BeautifulSoup(
                html,
                "lxml",
            )

        except Exception:
            return []

        links = {}

        for anchor in soup.find_all(
            "a",
            href=True,
        ):

            href = (
                anchor.get(
                    "href"
                )
                or ""
            ).strip()

            if not href:
                continue

            if href.startswith(
                (
                    "mailto:",
                    "tel:",
                    "javascript:",
                    "#",
                )
            ):
                continue

            absolute = (
                self.normalize_url(
                    urljoin(
                        base_url,
                        href,
                    )
                )
            )

            if not absolute:
                continue

            parsed = urlparse(
                absolute
            )

            if parsed.scheme not in {
                "http",
                "https",
            }:
                continue

            if absolute.lower().endswith(
                self.BINARY_EXTENSIONS
            ):
                continue

            if (
                self.root_domain(
                    absolute
                )
                != root_domain
            ):
                continue

            anchor_text = (
                anchor.get_text(
                    " ",
                    strip=True,
                )
            )

            score = (
                self.link_score(
                    absolute,
                    anchor_text,
                )
            )

            if score <= -100:
                continue

            previous = links.get(
                absolute
            )

            if (
                previous is None
                or score
                > previous[
                    "score"
                ]
            ):
                links[
                    absolute
                ] = {
                    "score":
                        score,
                    "text":
                        anchor_text,
                    "contact":
                        self.is_contact_link(
                            absolute,
                            anchor_text,
                        ),
                }

        ordered = sorted(
            links.items(),
            key=lambda item: (
                item[1][
                    "contact"
                ],
                item[1][
                    "score"
                ],
            ),
            reverse=True,
        )

        return [
            url
            for url, _
            in ordered
        ]

    # =========================================================
    # CONTACT PATH FALLBACK
    # =========================================================

    def build_common_contact_urls(
        self,
        base_url,
        root_domain,
    ):
        """
        Genera URLs típicas de contacto para utilizarlas
        como fallback.

        No significa que todas se visitarán:
        max_pages sigue limitando el crawler.
        """

        home = self.home_url(
            base_url
        )

        if not home:
            return []

        results = []

        for path in (
            self.COMMON_CONTACT_PATHS
        ):

            candidate = (
                self.normalize_url(
                    urljoin(
                        home,
                        path,
                    )
                )
            )

            if not candidate:
                continue

            if (
                self.root_domain(
                    candidate
                )
                != root_domain
            ):
                continue

            if candidate not in results:
                results.append(
                    candidate
                )

        return results

    # =========================================================
    # HTML SAVE
    # =========================================================

    def save_html(
        self,
        company_key,
        page_key,
        html,
    ):

        folder = (
            self.html_root
            / company_key
        )

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = (
            folder
            / f"{page_key}.html"
        )

        path.write_text(
            html,
            encoding="utf-8",
            errors="ignore",
        )

        return str(path)

    def save_pages(
        self,
        df,
    ):

        if not df.empty:

            df = (
                df.drop_duplicates(
                    subset=[
                        "PAGE_KEY",
                    ],
                    keep="last",
                )
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

        return df

    def save_seed_log(
        self,
        df,
    ):

        if not df.empty:

            df = (
                df.drop_duplicates(
                    subset=[
                        "SEED_KEY",
                    ],
                    keep="last",
                )
            )

        self.seed_log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        df.to_csv(
            self.seed_log_path,
            index=False,
            encoding="utf-8-sig",
        )

        return df

    # =========================================================
    # CRAWL ONE SEED
    # =========================================================

    def crawl_seed(
        self,
        seed,
        success_page_keys,
        max_pages,
    ):

        company_key = (
            seed[
                "COMPANY_KEY"
            ]
        )

        company_name = (
            seed[
                "COMPANY_NAME"
            ]
        )

        root_domain = (
            seed[
                "ROOT_DOMAIN"
            ]
        )

        seed_url = (
            self.normalize_url(
                seed[
                    "SEED_URL"
                ]
            )
        )

        seed_key = (
            seed[
                "SEED_KEY"
            ]
        )

        seed_type = (
            seed[
                "SEED_TYPE"
            ]
        )

        # Cola principal.
        queue = deque()

        # URL original siempre primero.
        queue.append(
            seed_url
        )

        # Si partimos desde una home o página principal,
        # preparamos rutas frecuentes de contacto como fallback.
        fallback_contacts = (
            self.build_common_contact_urls(
                seed_url,
                root_domain,
            )
        )

        visited_this_seed = (
            set()
        )

        queued = {
            seed_url
        }

        rows = []

        pages_fetched = 0

        had_success = False
        had_error = False

        discovered_real_contact = (
            False
        )

        while (
            queue
            and pages_fetched
            < max_pages
        ):

            page_url = (
                queue.popleft()
            )

            page_url = (
                self.normalize_url(
                    page_url
                )
            )

            if not page_url:
                continue

            if (
                page_url
                in visited_this_seed
            ):
                continue

            visited_this_seed.add(
                page_url
            )

            page_key = (
                self.page_key(
                    company_key,
                    page_url,
                )
            )

            # Esta página ya se descargó correctamente
            # anteriormente.
            if (
                page_key
                in success_page_keys
            ):
                continue

            print(
                "      -> "
                f"{page_url[:120]}"
            )

            result = (
                self.fetch_page(
                    page_url
                )
            )

            pages_fetched += 1

            html = result.get(
                "HTML",
                "",
            )

            links = []
            contact_links = []

            html_path = ""

            if (
                result.get(
                    "STATUS"
                )
                == "OK"
                and html
            ):
                had_success = True

                html_path = (
                    self.save_html(
                        company_key,
                        page_key,
                        html,
                    )
                )

                links = (
                    self.extract_internal_links(
                        html,
                        result.get(
                            "FINAL_URL",
                            page_url,
                        ),
                        root_domain,
                    )
                )

                contact_links = [
                    link
                    for link in links
                    if self.is_contact_link(
                        link
                    )
                ]

                if contact_links:
                    discovered_real_contact = (
                        True
                    )

                success_page_keys.add(
                    page_key
                )

                # -------------------------------------------------
                # CONTACTOS AL PRINCIPIO DE LA COLA
                # -------------------------------------------------

                # insertamos en orden inverso porque appendleft
                # coloca cada elemento al inicio.
                for link in reversed(
                    contact_links
                ):
                    if (
                        link
                        not in visited_this_seed
                        and link
                        not in queued
                    ):
                        queue.appendleft(
                            link
                        )

                        queued.add(
                            link
                        )

                # -------------------------------------------------
                # DESPUÉS EL RESTO DE LINKS PRIORIZADOS
                # -------------------------------------------------

                for link in links:

                    if (
                        link
                        in contact_links
                    ):
                        continue

                    if (
                        link
                        not in visited_this_seed
                        and link
                        not in queued
                    ):
                        queue.append(
                            link
                        )

                        queued.add(
                            link
                        )

                # -------------------------------------------------
                # FALLBACK
                # -------------------------------------------------
                #
                # Si todavía no encontramos ningún enlace real
                # de contacto, agregamos rutas típicas.
                #
                # Se ponen después de los contactos reales,
                # pero antes de terminar el crawl.
                # -------------------------------------------------

                if (
                    not discovered_real_contact
                    and pages_fetched == 1
                ):

                    for candidate in reversed(
                        fallback_contacts
                    ):
                        if (
                            candidate
                            not in visited_this_seed
                            and candidate
                            not in queued
                        ):
                            queue.appendleft(
                                candidate
                            )

                            queued.add(
                                candidate
                            )

            else:
                had_error = True

            rows.append(
                {
                    "PAGE_KEY":
                        page_key,

                    "SEED_KEY":
                        seed_key,

                    "COMPANY_KEY":
                        company_key,

                    "COMPANY_NAME":
                        company_name,

                    "ROOT_DOMAIN":
                        root_domain,

                    "SEED_TYPE":
                        seed_type,

                    "SEED_URL":
                        seed_url,

                    "PAGE_URL":
                        page_url,

                    "FINAL_URL":
                        result.get(
                            "FINAL_URL",
                            "",
                        ),

                    "HTTP_STATUS":
                        result.get(
                            "HTTP_STATUS",
                            "",
                        ),

                    "CONTENT_TYPE":
                        result.get(
                            "CONTENT_TYPE",
                            "",
                        ),

                    "TITLE":
                        result.get(
                            "TITLE",
                            "",
                        ),

                    "RENDER_MODE":
                        result.get(
                            "RENDER_MODE",
                            "requests",
                        ),

                    "NEEDS_JS":
                        (
                            "SI"
                            if result.get(
                                "NEEDS_JS"
                            )
                            else "NO"
                        ),

                    "VISIBLE_TEXT_LENGTH":
                        result.get(
                            "VISIBLE_TEXT_LENGTH",
                            0,
                        ),

                    "LINKS_FOUND":
                        len(
                            links
                        ),

                    "CONTACT_LINKS_FOUND":
                        len(
                            contact_links
                        ),

                    "HTML_PATH":
                        html_path,

                    "CRAWL_STATUS":
                        result.get(
                            "STATUS",
                            "ERROR",
                        ),

                    "ERROR":
                        result.get(
                            "ERROR",
                            "",
                        ),

                    "CRAWLED_AT":
                        datetime.now()
                        .isoformat(
                            timespec="seconds"
                        ),
                }
            )

            time.sleep(
                self.delay_seconds
            )

        if had_success:
            status = "PROCESSED"

        elif had_error:
            status = "ERROR"

        else:
            status = (
                "NO_NEW_PAGES"
            )

        return (
            rows,
            status,
        )

    # =========================================================
    # RUN
    # =========================================================

    def run(
        self,
        limit_companies=None,
        max_pages=5,
    ):

        seeds = (
            self.load_seeds(
                limit_companies=(
                    limit_companies
                )
            )
        )

        existing_pages = (
            self.load_pages()
        )

        seed_log = (
            self.load_seed_log()
        )

        # -----------------------------------------------------
        # SEEDS YA COMPLETADAS
        # -----------------------------------------------------

        processed_seed_keys = (
            set()
        )

        if not seed_log.empty:

            processed_seed_keys = set(
                seed_log[
                    seed_log[
                        "STATUS"
                    ].isin(
                        [
                            "PROCESSED",
                            "NO_NEW_PAGES",
                        ]
                    )
                ][
                    "SEED_KEY"
                ]
                .astype(str)
            )

        # -----------------------------------------------------
        # PÁGINAS YA DESCARGADAS OK
        # -----------------------------------------------------

        success_page_keys = (
            set()
        )

        if not existing_pages.empty:

            success_page_keys = set(
                existing_pages[
                    existing_pages[
                        "CRAWL_STATUS"
                    ]
                    == "OK"
                ][
                    "PAGE_KEY"
                ]
                .astype(str)
            )

        seeds[
            "IS_CACHED"
        ] = (
            seeds[
                "SEED_KEY"
            ]
            .isin(
                processed_seed_keys
            )
        )

        pending = seeds[
            ~seeds[
                "IS_CACHED"
            ]
        ].copy()

        print("=" * 70)
        print(
            " SITE CRAWLER V2 - "
            "CONTACT-FIRST + "
            "INCREMENTAL + PLAYWRIGHT"
        )
        print("=" * 70)

        print(
            f"Empresas seleccionadas : "
            f"{seeds['COMPANY_KEY'].nunique():,}"
        )

        print(
            f"Seeds seleccionadas     : "
            f"{len(seeds):,}"
        )

        print(
            f"Seeds en cache          : "
            f"{seeds['IS_CACHED'].sum():,}"
        )

        print(
            f"Seeds pendientes        : "
            f"{len(pending):,}"
        )

        print(
            f"Páginas cacheadas       : "
            f"{len(success_page_keys):,}"
        )

        print(
            f"Máx páginas/seed        : "
            f"{max_pages:,}"
        )

        print(
            f"Playwright              : "
            f"{'SI' if self.enable_js else 'NO'}"
        )

        print(
            "Objetivo principal      : "
            "CONTACTO / VENTAS / "
            "COMERCIAL / SOPORTE"
        )

        print("-" * 70)

        new_rows = []
        new_seed_logs = []

        for number, row in enumerate(
            pending.to_dict(
                "records"
            ),
            start=1,
        ):

            print()

            print(
                f"[Seed {number}/"
                f"{len(pending)}] "
                f"{row['COMPANY_NAME']} | "
                f"{row['SEED_TYPE']} | "
                f"{row['ROOT_DOMAIN']}"
            )

            before = len(
                new_rows
            )

            rows, status = (
                self.crawl_seed(
                    row,
                    success_page_keys,
                    max_pages=max_pages,
                )
            )

            new_rows.extend(
                rows
            )

            pages_new = (
                len(new_rows)
                - before
            )

            new_seed_logs.append(
                {
                    "SEED_KEY":
                        row[
                            "SEED_KEY"
                        ],

                    "COMPANY_KEY":
                        row[
                            "COMPANY_KEY"
                        ],

                    "COMPANY_NAME":
                        row[
                            "COMPANY_NAME"
                        ],

                    "ROOT_DOMAIN":
                        row[
                            "ROOT_DOMAIN"
                        ],

                    "SEED_TYPE":
                        row[
                            "SEED_TYPE"
                        ],

                    "SEED_URL":
                        row[
                            "SEED_URL"
                        ],

                    "STATUS":
                        status,

                    "PAGES_NEW":
                        pages_new,

                    "PROCESSED_AT":
                        datetime.now()
                        .isoformat(
                            timespec="seconds"
                        ),
                }
            )

            # Guardamos después de cada seed.
            # Si se corta el programa, no perdemos trabajo.
            pages_current = (
                pd.concat(
                    [
                        existing_pages,
                        pd.DataFrame(
                            new_rows
                        ),
                    ],
                    ignore_index=True,
                )
            )

            self.save_pages(
                pages_current
            )

            log_current = (
                pd.concat(
                    [
                        seed_log,
                        pd.DataFrame(
                            new_seed_logs
                        ),
                    ],
                    ignore_index=True,
                )
            )

            self.save_seed_log(
                log_current
            )

        final = (
            self.load_pages()
        )

        print()
        print("-" * 70)

        print(
            f"Páginas nuevas          : "
            f"{len(new_rows):,}"
        )

        print(
            f"Páginas acumuladas      : "
            f"{len(final):,}"
        )

        if not final.empty:

            print(
                f"HTML guardados          : "
                f"{final['HTML_PATH'].astype(str).str.strip().ne('').sum():,}"
            )

            print(
                f"Requests                : "
                f"{(final['RENDER_MODE'] == 'requests').sum():,}"
            )

            print(
                f"Playwright              : "
                f"{(final['RENDER_MODE'] == 'playwright').sum():,}"
            )

            print(
                f"Needs JS                : "
                f"{(final['NEEDS_JS'] == 'SI').sum():,}"
            )

            if (
                "CONTACT_LINKS_FOUND"
                in final.columns
            ):

                values = (
                    pd.to_numeric(
                        final[
                            "CONTACT_LINKS_FOUND"
                        ],
                        errors="coerce",
                    )
                    .fillna(0)
                )

                print(
                    f"Links contacto detectados: "
                    f"{int(values.sum()):,}"
                )

        print()

        print(
            self.output_path
        )

        print(
            self.seed_log_path
        )

        print(
            self.html_root
        )

        print("=" * 70)

        return self.output_path
