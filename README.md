## Amazon Web Crawler

A full-stack web application for searching Amazon products and scraping detailed reviews. Features a Flask backend API, web-based frontend interface, and export functionality for review data.

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

### Testing Notes (Updated 2025-09-16)

- Calling `/search` with "wireless earbuds" returned three Amazon browse/category URLs instead of product detail pages.
- Calling `/reviews` with either those browse URLs or a known product detail URL returned HTTP 200 but 0 parsed reviews.
- Likely reasons: Amazon frequently serves anti-bot HTML and the markup/selectors can change; reviews are often on dedicated URLs like `https://www.amazon.com/product-reviews/<ASIN>?pageNumber=...` and may require specific headers, referer, or cookies.

Suggested improvements:
- Normalize incoming product URLs to a product-reviews URL using the ASIN when possible.
- Update selectors to handle current Amazon review DOM variants.
- Strengthen request headers (rotate User-Agent, add `Referer`, accept gzip/br) and consider basic cookie handling.
- Consider backoff and clearer stop conditions for pagination.

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
