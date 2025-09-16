## Amazon Web Crawler

A full-stack web application for searching Amazon products and scraping detailed reviews. Features a Flask backend API, web-based frontend interface, and export functionality for review data.

<img width="1049" height="861" alt="Screenshot 2025-09-16 at 7 57 43 PM" src="https://github.com/user-attachments/assets/a1403663-deb3-4491-aa8e-906c490fef68" />



### Features

- **Product Search**: Search Amazon for products by keyword
- **Review Scraping**: Extract detailed reviews from product pages with optional star rating filtering
- **Web Interface**: User-friendly frontend for searching and viewing results
- **Data Export**: Export scraped reviews to Excel and CSV formats
- **Automated Setup**: One-click launcher script that handles environment setup

### Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/lfzhong/amazon_web_scrawler.git
   cd amazon_web_scrawler
   ```

2. **Run the application**:
   ```bash
   python run.py
   ```

   This will:
   - Check for virtual environment activation
   - Install Python dependencies
   - Install Playwright browsers
   - Start the backend server on `http://localhost:5001`
   - Open the frontend in your default browser

### Manual Setup (Alternative)

If you prefer manual setup:

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv && source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install
   ```

4. Start the backend:
   ```bash
   python backend/app.py
   ```

5. Open `index.html` in your browser to access the frontend.

### API Endpoints

The Flask backend provides the following REST API endpoints:

- `GET /search?keyword=<term>`: Returns up to 3 product links for the search term
- `GET /reviews?url=<product_url>&stars=<1-5 (optional)>`: Scrapes reviews from the given product URL, optionally filtering by star rating

Example API requests:
```bash
curl 'http://127.0.0.1:5001/search?keyword=wireless%20earbuds'

curl 'http://127.0.0.1:5001/reviews?url=https://www.amazon.com/dp/B07FZ8S74R'

curl 'http://127.0.0.1:5001/reviews?url=https://www.amazon.com/dp/B07FZ8S74R&stars=5'
```

### Export Functionality

After scraping reviews, data is automatically saved to Excel files in the `exports/` directory. Use the included export script to convert Excel files to CSV:

```bash
python export_reviews_csv.py
```

This extracts reviewer names, ratings, dates, review text, and helpful votes from all product sheets.

## __Architecture Overview__

This is a full-stack web application with a Flask backend API and vanilla JavaScript frontend for scraping Amazon product reviews.

## __Core Technologies__

- __Backend__: Python Flask with async Playwright for browser automation
- __Frontend__: HTML/CSS/JavaScript (no framework)
- __Scraping__: Playwright + BeautifulSoup for DOM parsing
- __Data Export__: Excel (openpyxl) and CSV formats
- __Browser Data__: Persistent Chrome browser storage for session management

## __Key Technical Components__

### __1. Backend Logic (Flask API)__

- __Routes__: `/search-reviews` (main endpoint), `/search`, `/product-reviews`, `/download-excel`, `/download-csv`

- __Scraping Strategy__:

  - Uses Playwright with headless Chrome
  - Implements anti-detection measures (user-agent rotation, viewport randomization, stealth mode)
  - Human-like behavior simulation (random delays, scrolling, mouse movements)
  - Multiple fallback selectors for Amazon's changing DOM structure

- __Data Processing__: Concurrent review extraction using asyncio

- __Export__: Automatic Excel generation with product-organized sheets

### __2. Frontend Logic (JavaScript)__

- __Search Interface__: Simple form with loading states and error handling
- __Results Display__: Product cards with expandable review lists
- __API Integration__: Fetches from `/search-reviews` endpoint
- __UX Features__: Keyboard shortcuts (Ctrl+K for search, Escape to clear), star ratings display

### __3. Scraping Logic__

- __Product Discovery__: Searches Amazon and extracts top 3 product URLs

- __Review Extraction__:

  - Tries product page first, then navigates to dedicated reviews page
  - Handles pagination and dynamic loading
  - Extracts: reviewer name, rating, date, text, helpful votes

- __Error Handling__: Graceful fallbacks when selectors fail or pages don't load

### __4. Data Export Logic__

- __Excel Generation__: Creates multi-sheet workbooks with summary and product-specific sheets
- __CSV Conversion__: Python script to extract reviews from Excel to CSV format
- __File Management__: Timestamped files in `/exports` directory

### __5. Browser Automation__

- __Playwright Setup__: Non-headless for debugging, with extensive anti-bot configuration
- __Session Persistence__: Uses `browser_data/` directory for Chrome profile storage
- __Stealth Measures__: Removes webdriver traces, randomizes fingerprints

## __Workflow__

1. User searches via frontend → Flask API receives request
2. Backend searches Amazon → extracts product URLs
3. Concurrent scraping of reviews from each product
4. Data aggregation and Excel export
5. Frontend displays results with download links

## __Challenges Addressed__

- Amazon's anti-scraping measures (bot detection, changing selectors)
- Dynamic content loading (scrolling, JavaScript rendering)
- Rate limiting (delays, concurrent processing limits)
- Data consistency (multiple selector fallbacks)
### Project Structure

```
amazon_web_crawler/
├── backend/
│   └── app.py              # Flask API server
├── exports/                # Exported review data (Excel/CSV)
├── debug_pages/            # Debug snapshots for troubleshooting
├── browser_data/           # Playwright browser data
├── index.html              # Frontend interface
├── script.js               # Frontend JavaScript
├── styles.css              # Frontend styles
├── run.py                  # Application launcher
├── export_reviews_csv.py   # Excel to CSV converter
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

### Dependencies

- Flask: Web framework
- Playwright: Browser automation for scraping
- openpyxl: Excel file handling
- requests: HTTP requests
- pandas: Data processing

### Disclaimer

Note: Scraping Amazon may violate their Terms of Service. Use responsibly and consider Amazon's official APIs for production applications.
