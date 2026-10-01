from __future__ import annotations

from playwright.sync_api import sync_playwright


class JSRenderer:
    """
    Renderiza páginas con JavaScript usando Chromium headless.

    Se usa como fallback cuando requests obtiene poco contenido
    o detectamos una SPA tipo React, Vite, Vue, Angular, etc.
    """

    def __init__(
        self,
        timeout_ms=25000,
        wait_ms=2500,
    ):
        self.timeout_ms = timeout_ms
        self.wait_ms = wait_ms

    def render(self, url):

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                )
            )

            try:

                response = page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=self.timeout_ms,
                )

                page.wait_for_timeout(
                    self.wait_ms
                )

                html = page.content()

                return {
                    "STATUS":
                        "OK",
                    "HTTP_STATUS":
                        response.status
                        if response
                        else "",
                    "FINAL_URL":
                        page.url,
                    "TITLE":
                        page.title(),
                    "HTML":
                        html,
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
                    "TITLE":
                        "",
                    "HTML":
                        "",
                    "ERROR":
                        str(exc),
                }

            finally:

                browser.close()
