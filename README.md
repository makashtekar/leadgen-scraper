# Lead Generation Scraper

A web scraper for lead generation targeting IndiaMart and JustDial. Includes a WebUI for managing scraper operations.

## Requirements

- Python 3.12+
- uv (recommended) or pip

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/makashtekar/leadgen-scraper.git
cd leadgen_scraper
```

### 2. Create Virtual Environment

Using uv (recommended):
```bash
uv venv
source .venv/bin/activate  # On macOS/Linux
.venv\Scripts\activate     # On Windows
```

Or using venv:
```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
.venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

Using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

## Running the Application

### Start the WebUI

```bash
python main.py
```

The WebUI will be available at: **http://localhost:8000**

### Login Credentials

- Username: `admin@gmail.com`
- Password: `test@1234`

## Usage

### WebUI

1. Open http://localhost:8000 in your browser
2. Enter login credentials (admin@gmail.com / test@1234)
3. View and manage scraped business contacts

### Running Scrapers from Command Line

You can also run scrapers directly:

```bash
python -c "
from src.leadgen_scraper.indiamart import IndiaMartScraper
from src.leadgen_scraper.justdial import JustDialScraper
from src.leadgen_scraper.database import Database

db = Database('business_contacts.db')

# Scrape IndiaMart
indiamart = IndiaMartScraper()
results = indiamart.scrape('textile')
for contact in results:
    db.add_contact(contact.to_db())

# Scrape JustDial
justdial = JustDialScraper()
results = justdial.scrape('textile')
for contact in results:
    db.add_contact(contact.to_db())

print('Scraping complete!')
"
```

## Project Structure

```
leadgen_scraper/
├── main.py                 # Entry point - starts WebUI
├── pyproject.toml          # Project configuration
├── src/
│   └── leadgen_scraper/
│       ├── __init__.py
│       ├── base_scraper.py # Base class for scrapers
│       ├── database.py    # SQLite database operations
│       ├── models.py      # Data models
│       ├── webui.py       # FastAPI WebUI
│       ├── indiamart.py   # IndiaMart scraper
│       └── justdial.py    # JustDial scraper
└── business_contacts.db   # SQLite database (created on first run)
```

## Adding New Scrapers

The scraper architecture is extensible. To add a new source:

1. Create a new class extending `BaseScraper`
2. Implement the `scrape()` method
3. Register it in your application

Example:
```python
from src.leadgen_scraper.base_scraper import BaseScraper
from src.leadgen_scraper.models import BusinessContact

class NewSourceScraper(BaseScraper):
    def scrape(self, keyword: str) -> list[BusinessContact]:
        # Implement scraping logic
        pass
```

## Environment Variables

- `DB_PATH` - Path to SQLite database (default: `business_contacts.db`)

## License

MIT