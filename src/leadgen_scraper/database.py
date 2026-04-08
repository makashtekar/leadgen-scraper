from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class BusinessContactDB(Base):
    __tablename__ = "business_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_name: Mapped[str] = mapped_column(String(500))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    products: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    search_keyword: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="indiamart")


class Database:
    def __init__(self, db_path: str | Path = "business_contacts.db"):
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_contact(self, contact: "BusinessContactDB") -> None:
        with self.Session() as session:
            session.add(contact)
            session.commit()

    def add_contacts(self, contacts: list["BusinessContactDB"]) -> None:
        with self.Session() as session:
            session.add_all(contacts)
            session.commit()

    def get_all_contacts(self) -> list["BusinessContactDB"]:
        with self.Session() as session:
            return list(session.query(BusinessContactDB).all())

    def search_contacts(self, keyword: str | None = None, source: str | None = None) -> list["BusinessContactDB"]:
        with self.Session() as session:
            query = session.query(BusinessContactDB)
            if keyword:
                query = query.where(BusinessContactDB.search_keyword == keyword)
            if source:
                query = query.where(BusinessContactDB.source == source)
            return list(query.all())

    def get_contacts_count(self) -> int:
        with self.Session() as session:
            return session.query(BusinessContactDB).count()
