## Amazon Web Crawler

Minimal Flask backend that scrapes Amazon search results and product reviews.

### Quick start

1. Create and activate a virtualenv (optional if you already have one):
   - macOS/Linux:
     ```bash
     python3 -m venv venv && . venv/bin/activate
     ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   FLASK_APP=backend.app:app FLASK_ENV=development flask run --host 127.0.0.1 --port 5000
   ```

### API

- `GET /search?keyword=<term>`: Returns up to 3 product links for the search term.
- `GET /reviews?url=<product_url>&stars=<1-5 (optional)>`: Scrapes reviews from the given product URL, optionally filtering by star rating.

Example requests:
```bash
curl 'http://127.0.0.1:5000/search?keyword=wireless%20earbuds'

curl 'http://127.0.0.1:5000/reviews?url=https://www.amazon.com/dp/B07FZ8S74R'

curl 'http://127.0.0.1:5000/reviews?url=https://www.amazon.com/dp/B07FZ8S74R&stars=5'
```

### Testing notes for /reviews (2025-09-14)

- Calling `/search` with "wireless earbuds" returned three Amazon browse/category URLs instead of product detail pages.
- Calling `/reviews` with either those browse URLs or a known product detail URL returned HTTP 200 but 0 parsed reviews.
- Likely reasons: Amazon frequently serves anti-bot HTML and the markup/selectors can change; reviews are often on dedicated URLs like `https://www.amazon.com/product-reviews/<ASIN>?pageNumber=...` and may require specific headers, referer, or cookies.

Suggested improvements:
- Normalize incoming product URLs to a product-reviews URL using the ASIN when possible.
- Update selectors to handle current Amazon review DOM variants.
- Strengthen request headers (rotate User-Agent, add `Referer`, accept gzip/br) and consider basic cookie handling.
- Consider backoff and clearer stop conditions for pagination.

Note: Scraping Amazon may violate their Terms of Service. Use responsibly.


