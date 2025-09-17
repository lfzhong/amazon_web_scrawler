## Amazon Web Crawler

A full-stack web application for searching Amazon products and scraping detailed reviews. Features a Flask backend API, web-based frontend interface, and export functionality for review data.

<img width="1049" height="861" alt="Screenshot 2025-09-16 at 7 57 43 PM" src="https://github.com/user-attachments/assets/57565bfd-243c-4606-ba4a-f646e8cfecd3" />



### Features

- **Product Search**: Search Amazon for products by keyword
- **Review Scraping**: Extract detailed reviews from product pages with optional star rating filtering
- **Web Interface**: User-friendly frontend for searching and viewing results
- **Data Export**: Export scraped reviews to Excel and CSV formats
- **Automated Setup**: One-click launcher script that handles environment setup

### Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/lfzhong/amazon_web_crawler.git
   cd amazon_web_crawler
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

### Authentication Configuration

The application supports optional Amazon authentication for enhanced scraping capabilities. Configure authentication by editing `backend/auth_config.json`:

```json
{
  "enabled": true,
  "credentials": {
    "email": "your-amazon-email@example.com",
    "password": "your-amazon-password"
  },
  "session_file": "amazon_session.json",
  "persistent_session": true
}
```

**Note**: Authentication is optional. The scraper works without login, but authenticated sessions may provide access to more reviews and reduce rate limiting.

### API Endpoints

The Flask backend provides the following REST API endpoints:

#### Core Functionality
- `GET /search-reviews?q=<keyword>&max_products=<number>`: Main endpoint that searches for products and scrapes their reviews
- `GET /product-reviews?url=<product_url>&max_reviews=<number>`: Scrapes reviews from a specific product URL
- `GET /download-excel/<filename>`: Downloads generated Excel files

#### Authentication Management
- `GET /auth-config`: Get current authentication configuration (without password)
- `POST /auth-config`: Update authentication configuration
- `POST /test-auth`: Test Amazon authentication with current credentials
- `GET /auth-status`: Check current authentication status
- `POST /clear-auth`: Clear stored authentication data and session cookies

#### Static File Serving
- `GET /`: Serves the frontend interface
- `GET /<path:filename>`: Serves static files (CSS, JS, etc.)

Example API requests:
```bash
# Search and scrape reviews
curl 'http://127.0.0.1:5001/search-reviews?q=wireless%20earbuds&max_products=3'

# Get reviews from specific product
curl 'http://127.0.0.1:5001/product-reviews?url=https://www.amazon.com/dp/B07FZ8S74R&max_reviews=50'

# Check authentication status
curl 'http://127.0.0.1:5001/auth-status'
```

### Export Functionality

After scraping reviews, data is automatically saved to Excel files in the `exports/` directory with timestamped filenames (e.g., `amazon_reviews_coffee_20250916_194622.xlsx`).

#### Current Export Files
The `exports/` directory contains generated Excel files with review data:
- `amazon_reviews_coffee_20250916_194622.xlsx`
- `amazon_reviews_coffee_20250916_195029.xlsx` 
- `amazon_reviews_tea_20250916_200507.xlsx`

#### Excel File Structure
Each Excel file contains:
- **Summary Sheet**: Overview of scraped data
- **Product Sheets**: Individual sheets for each product with detailed reviews
- **Review Data**: Reviewer names, ratings, dates, review text, and helpful votes

#### CSV Conversion
Use the included export script to convert Excel files to CSV format:

```bash
python export_reviews_csv.py
```

This extracts reviewer names, ratings, dates, review text, and helpful votes from all product sheets into a single CSV file.

## Architecture Overview

This is a full-stack web application with a Flask backend API and vanilla JavaScript frontend for scraping Amazon product reviews.

### Core Technologies

- **Backend**: Python Flask with async Playwright for browser automation
- **Frontend**: HTML/CSS/JavaScript (no framework)
- **Scraping**: Playwright + BeautifulSoup for DOM parsing
- **Data Export**: Excel (openpyxl) and CSV formats
- **Browser Data**: Persistent Chrome browser storage for session management

### Key Technical Components

#### 1. Backend Logic (Flask API)

- **Routes**: `/search-reviews` (main endpoint), `/product-reviews`, `/download-excel`, authentication endpoints
- **Scraping Strategy**:
  - Uses Playwright with headless Chrome
  - Implements anti-detection measures (user-agent rotation, viewport randomization, stealth mode)
  - Human-like behavior simulation (random delays, scrolling, mouse movements)
  - Multiple fallback selectors for Amazon's changing DOM structure
- **Data Processing**: Concurrent review extraction using asyncio
- **Export**: Automatic Excel generation with product-organized sheets

#### 2. Frontend Logic (JavaScript)

- **Search Interface**: Simple form with loading states and error handling
- **Results Display**: Product cards with expandable review lists
- **API Integration**: Fetches from `/search-reviews` endpoint
- **UX Features**: Keyboard shortcuts (Ctrl+K for search, Escape to clear), star ratings display

#### 3. Scraping Logic

- **Product Discovery**: Searches Amazon and extracts top 3 product URLs
- **Review Extraction**:
  - Tries product page first, then navigates to dedicated reviews page
  - Handles pagination and dynamic loading
  - Extracts: reviewer name, rating, date, text, helpful votes
- **Error Handling**: Graceful fallbacks when selectors fail or pages don't load

#### 4. Data Export Logic

- **Excel Generation**: Creates multi-sheet workbooks with summary and product-specific sheets
- **CSV Conversion**: Python script to extract reviews from Excel to CSV format
- **File Management**: Timestamped files in `/exports` directory

#### 5. Browser Automation

- **Playwright Setup**: Non-headless for debugging, with extensive anti-bot configuration
- **Session Persistence**: Uses `browser_data/` directory for Chrome profile storage
- **Stealth Measures**: Removes webdriver traces, randomizes fingerprints

### Workflow

1. User searches via frontend → Flask API receives request
2. Backend searches Amazon → extracts product URLs
3. Concurrent scraping of reviews from each product
4. Data aggregation and Excel export
5. Frontend displays results with download links

### Challenges Addressed

- Amazon's anti-scraping measures (bot detection, changing selectors)
- Dynamic content loading (scrolling, JavaScript rendering)
- Rate limiting (delays, concurrent processing limits)
- Data consistency (multiple selector fallbacks)

## Project Structure

```
amazon_web_crawler/
├── backend/
│   ├── app.py              # Flask API server
│   ├── auth_config.json    # Authentication configuration
│   └── amazon_session.json # Amazon session data
├── browser_data/           # Playwright browser data and Chrome profile
├── cursor_rules/           # IDE configuration files
├── exports/                # Exported review data (Excel/CSV files)
├── venv/                   # Python virtual environment
├── index.html              # Frontend interface
├── script.js               # Frontend JavaScript
├── styles.css              # Frontend styles
├── run.py                  # Application launcher script
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

### Dependencies

- **Flask**: Web framework for the REST API
- **flask-cors**: Cross-Origin Resource Sharing support for frontend-backend communication
- **Playwright**: Browser automation for scraping Amazon pages
- **BeautifulSoup4**: HTML parsing and data extraction
- **openpyxl**: Excel file generation and manipulation
- **requests**: HTTP requests for web scraping

### Disclaimer

Note: Scraping Amazon may violate their Terms of Service. Use responsibly and consider Amazon's official APIs for production applications.
