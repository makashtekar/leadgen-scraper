from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from leadgen_scraper.database import BusinessContactDB


class BusinessContact(BaseModel):
    business_name: str
    contact_phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    address: Optional[str] = None
    products: Optional[str] = None
    search_keyword: str
    source_url: Optional[str] = None
    source: str = Field(default="indiamart")

    def to_db(self) -> "BusinessContactDB":
        from leadgen_scraper.database import BusinessContactDB
        return BusinessContactDB(
            business_name=self.business_name,
            contact_phone=self.contact_phone,
            whatsapp_number=self.whatsapp_number,
            address=self.address,
            products=self.products,
            search_keyword=self.search_keyword,
            source_url=self.source_url,
            source=self.source,
        )


class ScrapeResult(BaseModel):
    success: bool
    keyword: str
    records_extracted: int = 0
    data: list[BusinessContact] = Field(default_factory=list)
    error: Optional[str] = None
