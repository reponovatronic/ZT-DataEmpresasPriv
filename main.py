from __future__ import annotations

import argparse

from src.search.query_builder import QueryBuilder
from src.search.search_manager import SearchManager

from src.validate.company_candidate_scorer import (
    CompanyCandidateScorer,
)

from src.validate.web_validator import (
    WebValidator,
)

from src.crawler.crawl_seed_builder import (
    CrawlSeedBuilder,
)

from src.crawler.site_crawler import (
    SiteCrawler,
)

from src.extract.email_extractor import (
    EmailExtractor,
)

from src.extract.email_cleaner import (
    EmailCleaner,
)

from src.export.final_exporter import (
    FinalExporter,
)


def main():

    parser = argparse.ArgumentParser(
        description=(
            "ZT-DataEmpresasPriv - "
            "Prospector de empresas privadas"
        )
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    # ==========================================
    # BUILD QUERIES
    # ==========================================

    query_parser = subparsers.add_parser(
        "build-queries"
    )

    query_parser.add_argument(
        "--niche",
        default=None,
    )

    # ==========================================
    # SEARCH
    # ==========================================

    search_parser = subparsers.add_parser(
        "search"
    )

    search_parser.add_argument(
        "--niche",
        default=None,
    )

    search_parser.add_argument(
        "--limit-queries",
        type=int,
        default=None,
    )

    # ==========================================
    # COMPANIES
    # ==========================================

    subparsers.add_parser(
        "companies"
    )

    # ==========================================
    # VALIDATE
    # ==========================================

    subparsers.add_parser(
        "validate-webs"
    )

    # ==========================================
    # CRAWL SEEDS
    # ==========================================

    subparsers.add_parser(
        "crawl-seeds"
    )

    # ==========================================
    # CRAWL
    # ==========================================

    crawl_parser = subparsers.add_parser(
        "crawl"
    )

    crawl_parser.add_argument(
        "--limit-companies",
        type=int,
        default=None,
    )

    crawl_parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
    )

    crawl_parser.add_argument(
        "--delay",
        type=float,
        default=0.35,
    )

    crawl_parser.add_argument(
        "--no-js",
        action="store_true",
    )

    # ==========================================
    # CONTACTS
    # ==========================================

    subparsers.add_parser(
        "extract-emails"
    )

    subparsers.add_parser(
        "clean-emails"
    )

    # ==========================================
    # EXPORT
    # ==========================================

    subparsers.add_parser(
        "export-final"
    )

    args = parser.parse_args()

    if args.command == "build-queries":

        QueryBuilder().run(
            niche=args.niche
        )

        return 0

    if args.command == "search":

        SearchManager().run(
            niche=args.niche,
            limit_queries=(
                args.limit_queries
            ),
        )

        return 0

    if args.command == "companies":

        CompanyCandidateScorer().run()

        return 0

    if args.command == "validate-webs":

        WebValidator().run()

        return 0

    if args.command == "crawl-seeds":

        CrawlSeedBuilder().run()

        return 0

    if args.command == "crawl":

        SiteCrawler(
            delay_seconds=args.delay,
            enable_js=not args.no_js,
        ).run(
            limit_companies=(
                args.limit_companies
            ),
            max_pages=args.max_pages,
        )

        return 0

    if args.command == "extract-emails":

        EmailExtractor().run()

        return 0

    if args.command == "clean-emails":

        EmailCleaner().run()

        return 0

    if args.command == "export-final":

        FinalExporter().run()

        return 0

    parser.print_help()

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
