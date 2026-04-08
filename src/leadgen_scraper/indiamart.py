import re
from typing import Any
from urllib.parse import quote

from parsel import Selector

from .base_scraper import BaseScraper
from .models import BusinessContact


class IndiaMartScraper(BaseScraper):
    BASE_URL = "https://dir.indiamart.com/cgi/ds2search.py"

    KEYWORDS = [
        "Garment Businesses",
        "Surplus garments",
        "Stocklot",
        "Warehouse clearance",
    ]

    def __init__(self, requests_per_second: float = 0.5, **kwargs):
        super().__init__(requests_per_second=requests_per_second, **kwargs)

    def build_search_url(self, keyword: str, page: int = 1) -> str:
        encoded_keyword = quote(keyword)
        return f"{self.BASE_URL}?query={encoded_keyword}&page={page}"

    def parse(self, html: str) -> list[dict[str, Any]]:
        selector = Selector(text=html)
        contacts = []

        listings = selector.css(".bw .rp .l .flt")
        for listing in listings:
            try:
                business_name = self._extract_text(listing.css(".pt .tt ::text"))
                contact_phone = self._extract_phone(listing)
                whatsapp = self._extract_whatsapp(listing)
                address = self._extract_text(listing.css(".cty ::text"))
                products = self._extract_text(listing.css(".p .pns ::text"))

                if business_name:
                    contacts.append(
                        BusinessContact(
                            business_name=business_name.strip(),
                            contact_phone=contact_phone,
                            whatsapp_number=whatsapp,
                            address=address.strip() if address else None,
                            products=products.strip() if products else None,
                            search_keyword="",
                            source="indiamart",
                        )
                    )
            except Exception:
                continue

        return [c.model_dump() for c in contacts]

    def _extract_text(self, selector) -> str | None:
        texts = selector.getall()
        if texts:
            return " ".join(t.strip() for t in texts if t.strip())
        return None

    def _extract_phone(self, listing) -> str | None:
        phone_elem = listing.css(".ph+ span::text, .ph span::text, [class*=ph]::text")
        for text in phone_elem.getall():
            phone = re.search(r"[\d\s\-\+\(\)]{7,20}", text)
            if phone:
                digits = re.sub(r"\D", "", phone.group())
                if len(digits) >= 10:
                    return digits
        return None

    def _extract_whatsapp(self, listing) -> str | None:
        whatsapp_elem = listing.css("[class*=wh] ::text, .whatsapp::text")
        for text in whatsapp_elem.getall():
            if "whatsapp" in text.lower() or "+" in text:
                digits = re.sub(r"\D", "", text)
                if 10 <= len(digits) <= 15:
                    return digits
        wa_link = listing.css("a[href*=wa]::attr(href)").get()
        if wa_link:
            digits = re.sub(r"\D", "", wa_link)
            if 10 <= len(digits) <= 15:
                return digits
        return None

    def get_total_pages(self, html: str) -> int:
        selector = Selector(text=html)
        page_links = selector.css(".pgn a::text, .pg a::text").getall()
        max_page = 1
        for p in page_links:
            try:
                page_num = int(p.strip())
                if page_num > max_page:
                    max_page = page_num
            except ValueError:
                continue
        return max_page

    def scrape_keyword(self, keyword: str, max_pages: int = 5) -> list[dict[str, Any]]:
        all_contacts = []
        first_url = self.build_search_url(keyword, page=1)

        first_html = self.get(first_url)
        if not first_html:
            return []

        total_pages = min(self.get_total_pages(first_html), max_pages)
        all_contacts.extend(self.parse(first_html))

        for page in range(2, total_pages + 1):
            url = self.build_search_url(keyword, page)
            html = self.get(url)
            if html:
                contacts = self.parse(html)
                for c in contacts:
                    c["search_keyword"] = keyword
                all_contacts.extend(contacts)

        return all_contacts

    def scrape_all(self, max_pages: int = 5) -> dict[str, list[dict[str, Any]]]:
        results = {}
        for keyword in self.KEYWORDS:
            results[keyword] = self.scrape_keyword(keyword, max_pages)
        return results
