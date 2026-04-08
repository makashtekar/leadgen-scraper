import os

import uvicorn
from loguru import logger

from leadgen_scraper.database import Database
from leadgen_scraper.indiamart import IndiaMartScraper
from leadgen_scraper.justdial import JustDialScraper
from leadgen_scraper.models import BusinessContact


def run_scrapers(db_path: str = "business_contacts.db", max_pages: int = 3):
    db = Database(db_path)
    total_saved = 0

    for scraper_cls in [IndiaMartScraper, JustDialScraper]:
        source_name = scraper_cls.__name__.replace("Scraper", "").lower()
        logger.info(f"Running {scraper_cls.__name__}...")

        scraper = scraper_cls(requests_per_second=0.3)
        try:
            results = scraper.scrape_all(max_pages=max_pages)
            for keyword, contacts in results.items():
                for contact_dict in contacts:
                    contact_dict["search_keyword"] = keyword
                    contact_dict["source"] = source_name
                    contact = BusinessContact(**contact_dict)
                    db.add_contact(contact.to_db())
                    total_saved += 1
                logger.info(f"Saved {len(contacts)} contacts for keyword: {keyword}")
        finally:
            scraper.close()

    logger.info(f"Total contacts saved: {total_saved}")
    return total_saved


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "scrape":
        max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        db_path = os.environ.get("DB_PATH", "business_contacts.db")
        run_scrapers(db_path, max_pages)
    else:
        uvicorn.run("leadgen_scraper.webui:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
