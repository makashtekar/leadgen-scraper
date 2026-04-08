import os
import asyncio
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from leadgen_scraper.database import BusinessContactDB, Database
from leadgen_scraper.models import BusinessContact

app = FastAPI(title="Lead Gen Scraper API", description="WebUI for managing scraper operations")
security = HTTPBasic()

DB_PATH = os.environ.get("DB_PATH", "business_contacts.db")
db = Database(DB_PATH)

SCRAPING_STATUS = {"status": "idle", "message": "", "progress": 0}


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


class ScrapeRequest(BaseModel):
    source: str
    keyword: Optional[str] = None
    max_pages: int = 3


class ScrapeResponse(BaseModel):
    status: str
    message: str
    contacts_added: int = 0


async def run_scraper_task(source: str, keyword: str, max_pages: int):
    global SCRAPING_STATUS
    try:
        if source == "indiamart":
            from leadgen_scraper.indiamart import IndiaMartScraper
            scraper = IndiaMartScraper()
            SCRAPING_STATUS = {"status": "running", "message": "Scraping IndiaMart...", "progress": 10}
            results = scraper.scrape_keyword(keyword, max_pages)
            SCRAPING_STATUS = {"status": "running", "message": f"Found {len(results)} contacts, saving to database...", "progress": 80}
            for contact_dict in results:
                contact = BusinessContact(**contact_dict)
                db.add_contact(contact.to_db())
            SCRAPING_STATUS = {"status": "completed", "message": f"Successfully scraped {len(results)} contacts from IndiaMart", "progress": 100}
        elif source == "justdial":
            from leadgen_scraper.justdial import JustDialScraper
            scraper = JustDialScraper()
            SCRAPING_STATUS = {"status": "running", "message": "Scraping JustDial...", "progress": 10}
            results = scraper.scrape_keyword(keyword, max_pages)
            SCRAPING_STATUS = {"status": "running", "message": f"Found {len(results)} contacts, saving to database...", "progress": 80}
            for contact_dict in results:
                contact = BusinessContact(**contact_dict)
                db.add_contact(contact.to_db())
            SCRAPING_STATUS = {"status": "completed", "message": f"Successfully scraped {len(results)} contacts from JustDial", "progress": 100}
        else:
            SCRAPING_STATUS = {"status": "error", "message": f"Unknown source: {source}", "progress": 0}
    except Exception as e:
        SCRAPING_STATUS = {"status": "error", "message": str(e), "progress": 0}


@app.get("/", response_class=HTMLResponse)
async def root(credentials: HTTPBasicCredentials = Depends(security)):
    verify_credentials(credentials)
    contacts = db.get_all_contacts()
    status_info = SCRAPING_STATUS
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lead Gen Scraper - Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            h1 { color: #333; }
            h2 { color: #555; }
            .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            table { border-collapse: collapse; width: 100%; background: white; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background: #4CAF50; color: white; }
            tr:nth-child(even) { background: #f2f2f2; }
            .stats { display: flex; gap: 20px; margin: 20px 0; }
            .stat-box { background: white; padding: 15px 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stat-box h3 { margin: 0; color: #4CAF50; font-size: 24px; }
            .stat-box p { margin: 5px 0 0 0; color: #666; }
            .btn { padding: 12px 24px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
            .btn:hover { background: #45a049; }
            .btn:disabled { background: #ccc; cursor: not-allowed; }
            .form-group { margin: 15px 0; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group select, .form-group input { padding: 8px; width: 200px; border: 1px solid #ddd; border-radius: 4px; }
            .status { padding: 10px 15px; border-radius: 5px; margin: 10px 0; }
            .status.idle { background: #e0e0e0; color: #666; }
            .status.running { background: #fff3cd; color: #856404; }
            .status.completed { background: #d4edda; color: #155724; }
            .status.error { background: #f8d7da; color: #721c24; }
            .progress-bar { width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; }
            .progress-fill { height: 100%; background: #4CAF50; transition: width 0.3s; }
        </style>
    </head>
    <body>
        <h1>Lead Gen Scraper Dashboard</h1>
        <div class="stats">
            <div class="stat-box">
                <h3>""" + str(len(contacts)) + """</h3>
                <p>Total Contacts</p>
            </div>
            <div class="stat-box">
                <h3 id="indiamart-count">""" + str(len([c for c in contacts if c.source == "indiamart"])) + """</h3>
                <p>IndiaMart</p>
            </div>
            <div class="stat-box">
                <h3 id="justdial-count">""" + str(len([c for c in contacts if c.source == "justdial"])) + """</h3>
                <p>JustDial</p>
            </div>
        </div>
        
        <div class="card">
            <h2>Run Scraper</h2>
            <form id="scrape-form">
                <div class="form-group">
                    <label for="source">Source:</label>
                    <select id="source" name="source">
                        <option value="indiamart">IndiaMart</option>
                        <option value="justdial">JustDial</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="keyword">Search Keyword:</label>
                    <input type="text" id="keyword" name="keyword" value="garment" placeholder="e.g., garment, textile">
                </div>
                <div class="form-group">
                    <label for="max-pages">Max Pages:</label>
                    <input type="number" id="max-pages" name="max-pages" value="3" min="1" max="10">
                </div>
                <button type="submit" class="btn" id="run-btn">Run Scraper</button>
            </form>
            <div id="status" class="status idle">Status: Idle</div>
            <div class="progress-bar" id="progress-container" style="display: none;">
                <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
            </div>
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
        
        <script>
        document.getElementById('scrape-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            const btn = document.getElementById('run-btn');
            const statusEl = document.getElementById('status');
            const progressContainer = document.getElementById('progress-container');
            const progressFill = document.getElementById('progress-fill');
            
            btn.disabled = true;
            btn.textContent = 'Running...';
            statusEl.className = 'status running';
            statusEl.textContent = 'Status: Starting...';
            progressContainer.style.display = 'block';
            progressFill.style.width = '0%';
            
            const formData = {
                source: document.getElementById('source').value,
                keyword: document.getElementById('keyword').value,
                max_pages: parseInt(document.getElementById('max-pages').value)
            };
            
            try {
                const response = await fetch('/api/scrape', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(formData)
                });
                const result = await response.json();
                
                statusEl.className = 'status ' + result.status;
                statusEl.textContent = 'Status: ' + result.message;
                progressFill.style.width = '100%';
                
                setTimeout(() => location.reload(), 2000);
            } catch (err) {
                statusEl.className = 'status error';
                statusEl.textContent = 'Error: ' + err.message;
                btn.disabled = false;
                btn.textContent = 'Run Scraper';
            }
        });
        
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                if (status.status === 'running') {
                    const statusEl = document.getElementById('status');
                    const progressFill = document.getElementById('progress-fill');
                    statusEl.className = 'status running';
                    statusEl.textContent = 'Status: ' + status.message;
                    progressFill.style.width = status.progress + '%';
                }
            } catch (e) {}
        }, 2000);
        </script>
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


@app.post("/api/scrape", dependencies=[Depends(verify_credentials)])
async def scrape(background_tasks: BackgroundTasks, request: ScrapeRequest) -> ScrapeResponse:
    global SCRAPING_STATUS
    if SCRAPING_STATUS["status"] == "running":
        raise HTTPException(status_code=409, detail="A scrape job is already running")
    
    keyword = request.keyword or "garment"
    background_tasks.add_task(run_scraper_task, request.source, keyword, request.max_pages)
    
    return ScrapeResponse(
        status="started",
        message=f"Starting {request.source} scrape for '{keyword}'"
    )


@app.get("/api/status", dependencies=[Depends(verify_credentials)])
async def get_status():
    return SCRAPING_STATUS