import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from leadgen_scraper.database import BusinessContactDB, Database
from leadgen_scraper.models import BusinessContact

app = FastAPI(title="Lead Gen Scraper API", description="WebUI for managing scraper operations")
security = HTTPBasic()

DB_PATH = os.environ.get("DB_PATH", "business_contacts.db")
db = Database(DB_PATH)


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    correct_username = credentials.username == "admin@gmail.com"
    correct_password = credentials.password == "test@1234"
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


class ContactResponse(BaseModel):
    id: int
    business_name: str
    contact_phone: Optional[str]
    whatsapp_number: Optional[str]
    address: Optional[str]
    products: Optional[str]
    search_keyword: str
    source_url: Optional[str]
    source: str

    @classmethod
    def from_db(cls, contact: BusinessContactDB) -> "ContactResponse":
        return cls(
            id=contact.id,
            business_name=contact.business_name,
            contact_phone=contact.contact_phone,
            whatsapp_number=contact.whatsapp_number,
            address=contact.address,
            products=contact.products,
            search_keyword=contact.search_keyword,
            source_url=contact.source_url,
            source=contact.source,
        )


@app.get("/", response_class=HTMLResponse)
async def root(credentials: HTTPBasicCredentials = Depends(security)):
    verify_credentials(credentials)
    contacts = db.get_all_contacts()
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lead Gen Scraper - Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            h1 { color: #333; }
            table { border-collapse: collapse; width: 100%; background: white; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background: #4CAF50; color: white; }
            tr:nth-child(even) { background: #f2f2f2; }
            .stats { margin: 20px 0; padding: 15px; background: white; border-radius: 5px; }
            .btn { padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Lead Gen Scraper Dashboard</h1>
        <div class="stats">
            <h2>Total Contacts: """
    html += str(len(contacts))
    html += """</h2>
        </div>
        <h2>Business Contacts</h2>
        <table>
            <tr>
                <th>Business Name</th>
                <th>Phone</th>
                <th>WhatsApp</th>
                <th>Source</th>
                <th>Keyword</th>
                <th>Products</th>
            </tr>
    """
    for contact in contacts:
        html += f"""
            <tr>
                <td>{contact.business_name}</td>
                <td>{contact.contact_phone or ''}</td>
                <td>{contact.whatsapp_number or ''}</td>
                <td>{contact.source}</td>
                <td>{contact.search_keyword}</td>
                <td>{contact.products or ''}</td>
            </tr>
        """
    html += """
        </table>
    </body>
    </html>
    """
    return html


@app.get("/api/contacts", dependencies=[Depends(verify_credentials)])
async def get_contacts(keyword: Optional[str] = None, source: Optional[str] = None) -> list[ContactResponse]:
    contacts = db.search_contacts(keyword=keyword, source=source)
    return [ContactResponse.from_db(c) for c in contacts]


@app.get("/api/contacts/count", dependencies=[Depends(verify_credentials)])
async def get_contacts_count() -> int:
    return db.get_contacts_count()


@app.post("/api/contacts", dependencies=[Depends(verify_credentials)])
async def add_contact(contact: BusinessContact) -> ContactResponse:
    db_contact = contact.to_db()
    db.add_contact(db_contact)
    return ContactResponse.from_db(db_contact)
