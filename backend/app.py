import asyncio
import random
import logging
import os
import tempfile
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import csv
from openpyxl import Workbook

# ---------------- Logging setup ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------- User-Agent pool ----------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) "
    "Gecko/20100101 Firefox/123.0",
]

def create_app() -> Flask:
    app = Flask(__name__)

    # ---------------- Helper: Generate Excel file from review data ----------------
    def generate_excel_file(search_term, products):
        """Generate Excel file with review data organized by product"""

        # Create a new workbook and select the active worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Amazon Reviews"

        # Define headers
        headers = ['Product', 'Reviewer Name', 'Rating', 'Date', 'Review Text', 'Helpful Votes']
        for col_num, header in enumerate(headers, 1):
            ws.cell(row=1, column=col_num, value=header)

        # Start from row 2
        row_num = 2

        # Add summary information
        ws.cell(row=row_num, column=1, value='SUMMARY')
        ws.cell(row=row_num, column=2, value=f'Search Term: {search_term}')
        ws.cell(row=row_num, column=4, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        row_num += 1

        # Process each product
        for i, product in enumerate(products, 1):
            # Add product header
            product_title = product["title"][:50] + "..." if len(product["title"]) > 50 else product["title"]
            ws.cell(row=row_num, column=1, value=f'PRODUCT {i}: {product_title}')
            ws.cell(row=row_num, column=2, value=product["url"])
            ws.cell(row=row_num, column=3, value=f'Reviews: {product["reviews_count"]}')
            ws.cell(row=row_num, column=4, value='Success: Yes' if product["success"] else 'Success: No')
            row_num += 1

            # Add reviews for this product
            reviews = product.get("reviews", [])
            for review in reviews:
                ws.cell(row=row_num, column=1, value=product_title)
                ws.cell(row=row_num, column=2, value=review.get("reviewer_name", ""))
                ws.cell(row=row_num, column=3, value=review.get("rating", ""))
                ws.cell(row=row_num, column=4, value=review.get("date", ""))
                ws.cell(row=row_num, column=5, value=review.get("text", ""))
                ws.cell(row=row_num, column=6, value=review.get("helpful_votes", ""))
                row_num += 1

        # Save to exports directory
        exports_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"amazon_reviews_{search_term.replace(' ', '_')}_{timestamp}.xlsx"
        filepath = os.path.join(exports_dir, filename)

        # Save the workbook
        wb.save(filepath)

        return filepath, filename

    # ---------------- Helper: Human-like delay ----------------
    async def human_delay(min_ms=1000, max_ms=3000):
        await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)

    # ---------------- Helper: Human-like scrolling ----------------
    async def human_scroll(page, max_scrolls=3):
        """Perform human-like scrolling to load dynamic content and appear more natural"""
        try:
            # Get page height
            page_height = await page.evaluate("document.body.scrollHeight")

            for i in range(random.randint(1, max_scrolls)):
                # Random scroll amount (300-800px)
                scroll_amount = random.randint(300, 800)
                current_scroll = await page.evaluate("window.pageYOffset")

                # Sometimes use smooth scrolling, sometimes instant
                if random.choice([True, False]):
                    # Smooth scroll
                    await page.evaluate(f"""
                        window.scrollTo({{
                            top: {current_scroll + scroll_amount},
                            behavior: 'smooth'
                        }});
                    """)
                    await human_delay(800, 1500)  # Wait for smooth scroll
                else:
                    # Instant scroll
                    await page.evaluate(f"window.scrollTo(0, {current_scroll + scroll_amount})")
                    await human_delay(300, 800)  # Shorter wait for instant scroll

                # Random pause to simulate reading
                if random.random() < 0.3:  # 30% chance
                    await human_delay(1000, 3000)

            # Sometimes scroll back up a bit (20% chance)
            if random.random() < 0.2:
                back_scroll = random.randint(100, 300)
                current_scroll = await page.evaluate("window.pageYOffset")
                await page.evaluate(f"window.scrollTo(0, {max(0, current_scroll - back_scroll)})")
                await human_delay(500, 1000)

            logger.info(f"🔄 Performed {max_scrolls} scroll actions to load dynamic content")

        except Exception as e:
            logger.warning(f"⚠️ Scrolling failed: {str(e)}")

    # ---------------- Helper: Extract product reviews from page ----------------
    async def extract_product_reviews(product_url, max_reviews=10):
        """Extract customer reviews from a product page - first tries product page reviews, then navigates to reviews page"""
        browser = None
        playwright = None
        page = None
        try:
            browser, playwright, page = await get_browser(headless=False)
            logger.info(f"📝 Getting reviews for: {product_url}")
            await page.goto(product_url, timeout=60000)
            await page.wait_for_load_state("domcontentloaded")
            await human_delay(2000, 4000)

            # Add human-like scrolling to load dynamic content
            await human_scroll(page, max_scrolls=2)

            # Helper function to extract reviews from soup
            def extract_reviews_from_soup(soup, max_reviews=None):
                reviews = []
                review_containers = []

                # Try multiple selectors for review containers
                review_selectors = [
                    'li[data-hook="review"]',
                    '.review',
                    '[data-hook="review"]',
                    '.a-section.review'
                ]

                for selector in review_selectors:
                    containers = soup.select(selector)
                    if containers:
                        logger.info(f"✅ Found {len(containers)} review containers with selector: {selector}")
                        review_containers = containers
                        break

                if not review_containers:
                    logger.warning("⚠️ No review containers found")
                    return reviews

                logger.info(f"🔍 Found {len(review_containers)} review containers")

                # Limit reviews if max_reviews is specified
                containers_to_process = review_containers
                if max_reviews is not None:
                    containers_to_process = review_containers[:max_reviews]

                for i, review in enumerate(containers_to_process):
                    try:
                        # Extract review text
                        review_text = ""
                        text_selectors = [
                            '[data-hook="review-body"]',
                            '.review-text-content',
                            '.a-expander-content',
                            '[data-hook="review-collapsed"]'
                        ]
                        for selector in text_selectors:
                            text_el = review.select_one(selector)
                            if text_el:
                                review_text = text_el.get_text(strip=True)
                                break

                        # Extract rating
                        rating = ""
                        rating_selectors = [
                            '[data-hook="review-star-rating"] .a-icon-alt',
                            '.a-icon-star .a-icon-alt',
                            '[data-hook="cmps-review-star-rating"]'
                        ]
                        for selector in rating_selectors:
                            rating_el = review.select_one(selector)
                            if rating_el:
                                rating_text = rating_el.get_text(strip=True)
                                import re
                                match = re.search(r"(\d+\.?\d*)", rating_text)
                                if match:
                                    rating = match.group(1)
                                    break

                        # Extract reviewer name
                        reviewer_name = ""
                        name_selectors = [
                            '[data-hook="review-author"]',
                            '.a-profile-name',
                            '[data-hook="cmps-reviewer-name"]'
                        ]
                        for selector in name_selectors:
                            name_el = review.select_one(selector)
                            if name_el:
                                reviewer_name = name_el.get_text(strip=True)
                                break

                        # Extract review date
                        review_date = ""
                        date_selectors = [
                            '[data-hook="review-date"]',
                            '.review-date',
                            '[data-hook="cmps-review-date"]'
                        ]
                        for selector in date_selectors:
                            date_el = review.select_one(selector)
                            if date_el:
                                review_date = date_el.get_text(strip=True)
                                break

                        # Extract helpful votes
                        helpful_votes = ""
                        helpful_selectors = [
                            '[data-hook="helpful-vote-statement"]',
                            '.helpful-votes',
                            '[data-hook="cmps-helpful-vote-statement"]'
                        ]
                        for selector in helpful_selectors:
                            helpful_el = review.select_one(selector)
                            if helpful_el:
                                helpful_votes = helpful_el.get_text(strip=True)
                                break

                        if review_text:  # Only add reviews that have content
                            reviews.append({
                                "reviewer_name": reviewer_name,
                                "rating": rating,
                                "date": review_date,
                                "text": review_text,
                                "helpful_votes": helpful_votes
                            })

                    except Exception as e:
                        logger.warning(f"⚠️ Error extracting review {i+1}: {str(e)}")
                        continue

                return reviews

            # First, try to extract reviews directly from the product page
            soup = BeautifulSoup(await page.content(), "html.parser")
            # Extract all available reviews from product page
            reviews = extract_reviews_from_soup(soup)

            if reviews:
                result = {
                    "url": product_url,
                    "total_reviews_found": len(reviews),
                    "reviews": reviews,
                    "success": True,
                    "source": "product_page"
                }
                logger.info(f"✅ Extracted {len(reviews)} reviews from product page")
                return result

            # If no reviews found on product page, try to get reviews - first try clicking review link, then try direct navigation
            reviews_loaded = False

            # Method 1: Try clicking review link
            try:
                # Try multiple selectors for the review link
                review_selectors = [
                    "a#acrCustomerReviewLink",
                    "a[href*='customerReviews']",
                    "[data-hook='see-all-reviews-link']",
                    "a.a-link-emphasis[href*='reviews']",
                    "a[href*='product-reviews']"
                ]

                review_link = None
                for selector in review_selectors:
                    try:
                        link = page.locator(selector)
                        if await link.count() > 0:
                            review_link = link
                            logger.info(f"✅ Found review link with selector: {selector}")
                            break
                    except:
                        continue

                if review_link:
                    await review_link.click()
                    logger.info("✅ Clicked customer review link")

                    # Wait for reviews to load
                    await page.wait_for_load_state("networkidle")
                    await human_delay(2000, 4000)

                    # Sometimes reviews load in a modal or overlay
                    await human_scroll(page, max_scrolls=1)
                    reviews_loaded = True
                else:
                    logger.warning("⚠️ No review link found with any selector")

            except Exception as e:
                logger.warning(f"⚠️ Could not click review link: {str(e)}")

            # Method 2: If clicking didn't work, try navigating directly to reviews page
            if not reviews_loaded:
                try:
                    # Extract product ID from URL
                    import re
                    product_id_match = re.search(r'/dp/([A-Z0-9]+)', product_url)
                    if product_id_match:
                        product_id = product_id_match.group(1)
                        reviews_url = f"https://www.amazon.com/product-reviews/{product_id}"
                        logger.info(f"🔄 Trying direct navigation to: {reviews_url}")

                        await page.goto(reviews_url, timeout=60000)
                        await page.wait_for_load_state("domcontentloaded")
                        await human_delay(3000, 5000)  # Increased wait time

                        # Wait for network to be idle (JavaScript loading reviews)
                        await page.wait_for_load_state("networkidle")
                        await human_delay(2000, 3000)

                        # Try to wait for review elements to appear
                        try:
                            await page.wait_for_selector('[data-hook="review"], .review, .a-section.review', timeout=10000)
                            logger.info("✅ Review elements found on page")
                        except:
                            logger.warning("⚠️ Review elements not found within timeout")

                        await human_scroll(page, max_scrolls=3)  # More scrolling to trigger loading
                        await human_delay(1000, 2000)

                        reviews_loaded = True
                        logger.info("✅ Navigated to reviews page directly")
                    else:
                        logger.warning("⚠️ Could not extract product ID for direct navigation")

                except Exception as e:
                    logger.warning(f"⚠️ Direct navigation to reviews failed: {str(e)}")

            soup = BeautifulSoup(await page.content(), "html.parser")

            # Debug: Log page structure to identify correct selectors
            logger.info(f"🔍 Page title: {soup.title.get_text() if soup.title else 'No title'}")
            logger.info(f"🔍 Body classes: {soup.body.get('class') if soup.body else 'No body'}")
            logger.info(f"🔍 Looking for review elements...")

            reviews = extract_reviews_from_soup(soup, max_reviews)

            result = {
                "url": product_url,
                "total_reviews_found": len(reviews),
                "reviews": reviews,
                "success": True
            }

            logger.info(f"✅ Extracted {len(reviews)} reviews for product")
            return result

        except Exception as e:
            logger.error(f"❌ Error getting product reviews for {product_url}: {str(e)}")
            return {
                "url": product_url,
                "reviews": [],
                "success": False,
                "error": str(e)
            }
        finally:
            # Safely close browser and playwright
            try:
                if browser:
                    await browser.close()
                if playwright:
                    await playwright.stop()
            except Exception as e:
                logger.warning(f"⚠️ Error closing browser/playwright: {str(e)}")

    # ---------------- Helper: Extract product details from page ----------------
    async def extract_product_details(product_url):
        """Extract product details from a single product page"""
        browser, playwright, page = await get_browser(headless=False)
        try:
            logger.info(f"📦 Getting details for: {product_url}")
            await page.goto(product_url, timeout=60000)
            await page.wait_for_load_state("domcontentloaded")
            await human_delay(2000, 4000)

            # Add human-like scrolling to load dynamic content
            await human_scroll(page, max_scrolls=2)

            soup = BeautifulSoup(await page.content(), "html.parser")

            # Extract title
            title = ""
            title_selectors = [
                "#productTitle",
                "#title",
                ".a-size-large.product-title-word-break",
                "h1.a-size-large"
            ]
            for selector in title_selectors:
                title_el = soup.select_one(selector)
                if title_el:
                    title = title_el.get_text(strip=True)
                    break

            # Extract price
            price = ""
            price_selectors = [
                ".a-price .a-offscreen",
                "#priceblock_ourprice",
                "#priceblock_dealprice",
                "#priceblock_saleprice",
                ".a-price-whole",
                ".a-color-price",
                "#corePrice_feature_div .a-price .a-offscreen",
                "#corePriceDisplay_desktop_feature_div .a-price-whole",
                "#corePriceDisplay_desktop_feature_div .a-price-fraction",
                ".a-price .a-offscreen:first-child",
                "#snsPrice .a-price .a-offscreen",
                ".apexPriceToPay .a-offscreen"
            ]
            for selector in price_selectors:
                price_el = soup.select_one(selector)
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    # Clean up price text
                    if price_text and ("$" in price_text or "CDN$" in price_text):
                        price = price_text
                        break

            # Extract rating
            rating = ""
            rating_selectors = [
                ".a-icon-star-small .a-icon-alt",
                ".a-icon-star .a-icon-alt",
                "#acrPopover .a-icon-alt",
                ".review-rating",
                "#averageCustomerReviews .a-icon-alt",
                ".a-declarative[data-action='acrStarsLink'] .a-icon-alt",
                "#acrPopover [data-cy='reviews-ratings-date']"
            ]
            for selector in rating_selectors:
                rating_el = soup.select_one(selector)
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    # Extract number from "4.5 out of 5 stars"
                    import re
                    match = re.search(r"(\d+\.?\d*)", rating_text)
                    if match:
                        rating = match.group(1)
                        break

            # Extract review count
            review_count = ""
            review_selectors = [
                "#acrCustomerReviewText",
                ".a-size-base",
                "a[href*='customerReviews']",
                "#acrCustomerReviewLink",
                "[data-cy='reviews-ratings-count']",
                ".a-link-emphasis"
            ]
            for selector in review_selectors:
                review_el = soup.select_one(selector)
                if review_el:
                    review_text = review_el.get_text(strip=True)
                    # Look for patterns like "1,234 ratings" or "1,234 customer reviews"
                    import re
                    match = re.search(r"([\d,]+)", review_text)
                    if match:
                        review_count = match.group(1)
                        break

            result = {
                "url": product_url,
                "title": title,
                "price": price,
                "rating": rating,
                "review_count": review_count,
                "success": True
            }

            logger.info(f"✅ Extracted details: {title[:50]}... | Price: {price} | Rating: {rating} | Reviews: {review_count}")
            return result

        except Exception as e:
            logger.error(f"❌ Error getting product details for {product_url}: {str(e)}")
            return {
                "url": product_url,
                "title": "",
                "price": "",
                "rating": "",
                "review_count": "",
                "success": False,
                "error": str(e)
            }
        finally:
            await browser.close()
            await playwright.stop()

    # ---------------- Helper: Start browser with rotation ----------------
    async def get_browser(headless=False):  # Changed to non-headless for testing
        ua = random.choice(USER_AGENTS)
        viewport = {
            "width": random.randint(1280, 1920),
            "height": random.randint(720, 1080),
        }

        logger.info(f"🌐 Using UA: {ua[:60]}..., viewport={viewport}")

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--user-agent=" + ua,
            ]
        )
        context = await browser.new_context(
            user_agent=ua,
            locale="en-US",
            timezone_id="America/New_York",
            viewport=viewport,
            ignore_https_errors=True,
        )

        # Add more stealth measures
        page = await context.new_page()
        await page.evaluate("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

        return browser, playwright, page



    # ---------------- Route: Get product details ----------------
    @app.route("/product-details")
    def product_details():
        product_url = request.args.get("url", "").strip()
        if not product_url:
            return jsonify({"error": "Missing product URL", "success": False}), 400

        # Basic validation for Amazon URLs
        if not ("amazon.com" in product_url and ("/dp/" in product_url or "/gp/product/" in product_url)):
            return jsonify({"error": "Invalid Amazon product URL", "success": False}), 400

        async def run():
            browser, playwright, page = await get_browser(headless=False)
            try:
                logger.info(f"📦 Getting details for: {product_url}")
                await page.goto(product_url, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                await human_delay(2000, 4000)

                # Add human-like scrolling to load dynamic content
                await human_scroll(page, max_scrolls=2)

                soup = BeautifulSoup(await page.content(), "html.parser")

                # Debug: Log some HTML content to identify selectors
                logger.info(f"🔍 Page title: {soup.title.get_text() if soup.title else 'No title'}")
                logger.info(f"🔍 First few price-related elements: {len(soup.select('.a-price'))}")
                logger.info(f"🔍 First few rating elements: {len(soup.select('.a-icon-star'))}")
                logger.info(f"🔍 Sample HTML around price: {str(soup.select_one('.a-price'))[:200] if soup.select_one('.a-price') else 'No .a-price found'}")

                # Extract title
                title = ""
                title_selectors = [
                    "#productTitle",
                    "#title",
                    ".a-size-large.product-title-word-break",
                    "h1.a-size-large"
                ]
                for selector in title_selectors:
                    title_el = soup.select_one(selector)
                    if title_el:
                        title = title_el.get_text(strip=True)
                        break

                # Extract price
                price = ""
                price_selectors = [
                    ".a-price .a-offscreen",
                    "#priceblock_ourprice",
                    "#priceblock_dealprice",
                    "#priceblock_saleprice",
                    ".a-price-whole",
                    ".a-color-price",
                    "#corePrice_feature_div .a-price .a-offscreen",
                    "#corePriceDisplay_desktop_feature_div .a-price-whole",
                    "#corePriceDisplay_desktop_feature_div .a-price-fraction",
                    ".a-price .a-offscreen:first-child",
                    "#snsPrice .a-price .a-offscreen",
                    ".apexPriceToPay .a-offscreen"
                ]
                for selector in price_selectors:
                    price_el = soup.select_one(selector)
                    if price_el:
                        price_text = price_el.get_text(strip=True)
                        # Clean up price text
                        if price_text and ("$" in price_text or "CDN$" in price_text):
                            price = price_text
                            break

                # Extract rating
                rating = ""
                rating_selectors = [
                    ".a-icon-star-small .a-icon-alt",
                    ".a-icon-star .a-icon-alt",
                    "#acrPopover .a-icon-alt",
                    ".review-rating",
                    "#averageCustomerReviews .a-icon-alt",
                    ".a-declarative[data-action='acrStarsLink'] .a-icon-alt",
                    "#acrPopover [data-cy='reviews-ratings-date']"
                ]
                for selector in rating_selectors:
                    rating_el = soup.select_one(selector)
                    if rating_el:
                        rating_text = rating_el.get_text(strip=True)
                        # Extract number from "4.5 out of 5 stars"
                        import re
                        match = re.search(r"(\d+\.?\d*)", rating_text)
                        if match:
                            rating = match.group(1)
                            break

                # Extract review count
                review_count = ""
                review_selectors = [
                    "#acrCustomerReviewText",
                    ".a-size-base",
                    "a[href*='customerReviews']",
                    "#acrCustomerReviewLink",
                    "[data-cy='reviews-ratings-count']",
                    ".a-link-emphasis"
                ]
                for selector in review_selectors:
                    review_el = soup.select_one(selector)
                    if review_el:
                        review_text = review_el.get_text(strip=True)
                        # Look for patterns like "1,234 ratings" or "1,234 customer reviews"
                        import re
                        match = re.search(r"([\d,]+)", review_text)
                        if match:
                            review_count = match.group(1)
                            break

                result = {
                    "url": product_url,
                    "title": title,
                    "price": price,
                    "rating": rating,
                    "review_count": review_count,
                    "success": True
                }

                logger.info(f"✅ Extracted details: {title[:50]}... | Price: {price} | Rating: {rating} | Reviews: {review_count}")
                return result

            except Exception as e:
                logger.error(f"❌ Error getting product details: {str(e)}")
                return {
                    "url": product_url,
                    "error": f"Failed to extract product details: {str(e)}",
                    "success": False
                }
            finally:
                await browser.close()
                await playwright.stop()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run())

    # ---------------- Route: Search for top 3 product links ----------------
    @app.route("/search")
    def search():
        keyword = (request.args.get("q") or "").strip()
        if not keyword:
            return jsonify({"error": "Missing search keyword"}), 400

        async def run():
            browser, playwright, page = await get_browser(headless=True)
            try:
                # Search Amazon
                search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
                logger.info(f"🔍 Searching for: {keyword}")
                await page.goto(search_url, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                await human_delay(2000, 4000)

                # Add scrolling to load more search results
                await human_scroll(page, max_scrolls=1)

                try:
                    await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=15000)
                except:
                    html = await page.content()
                    logger.error("❌ No search results loaded")
                    return {"error": "No search results loaded"}

                soup = BeautifulSoup(await page.content(), "html.parser")
                product_containers = (
                    soup.select('[data-component-type="s-search-result"]')
                    or soup.select('[data-asin][data-index]')
                    or soup.select('.s-result-item')
                )

                logger.info(f"🔍 Found {len(product_containers)} product containers")

                products = []
                for i, container in enumerate(product_containers[:3]):  # Only top 3
                    logger.info(f"Processing container {i+1}: {str(container)[:200]}...")

                    # Try multiple selectors for title and link
                    title_el = (
                        container.select_one('h2 a span') or
                        container.select_one('h2 span') or
                        container.select_one('.a-text-normal') or
                        container.select_one('span.a-text-normal')
                    )

                    link_el = (
                        container.select_one('h2 a') or
                        container.select_one('a.a-link-normal') or
                        container.select_one('a[href*="/dp/"]')
                    )

                    if not (title_el and link_el):
                        logger.warning(f"⚠️ Container {i+1}: Missing title or link")
                        continue

                    product_url = link_el.get("href", "")
                    if product_url.startswith("/"):
                        product_url = f"https://www.amazon.com{product_url}"

                    title_text = title_el.get_text(strip=True)
                    products.append({
                        "title": title_text,
                        "url": product_url
                    })
                    logger.info(f"✅ Found product {i+1}: {title_text[:50]}...")

                return {"keyword": keyword, "products": products}

            finally:
                await browser.close()
                await playwright.stop()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run())

    # ---------------- Route: Search with detailed product information ----------------
    @app.route("/search-detailed")
    def search_detailed():
        keyword = (request.args.get("q") or "").strip()
        if not keyword:
            return jsonify({"error": "Missing search keyword"}), 400

        async def run():
            browser, playwright, page = await get_browser(headless=True)
            try:
                # Search Amazon
                search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
                logger.info(f"🔍 Detailed search for: {keyword}")
                await page.goto(search_url, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                await human_delay(2000, 4000)

                # Add scrolling to load more search results
                await human_scroll(page, max_scrolls=1)

                try:
                    await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=15000)
                except:
                    html = await page.content()
                    logger.error("❌ No search results loaded")
                    return {"error": "No search results loaded"}

                soup = BeautifulSoup(await page.content(), "html.parser")
                product_containers = (
                    soup.select('[data-component-type="s-search-result"]')
                    or soup.select('[data-asin][data-index]')
                    or soup.select('.s-result-item')
                )

                logger.info(f"🔍 Found {len(product_containers)} product containers")

                # Extract basic product info (titles and URLs)
                basic_products = []
                for i, container in enumerate(product_containers[:3]):  # Only top 3
                    logger.info(f"Processing container {i+1}: {str(container)[:200]}...")

                    # Try multiple selectors for title and link
                    title_el = (
                        container.select_one('h2 a span') or
                        container.select_one('h2 span') or
                        container.select_one('.a-text-normal') or
                        container.select_one('span.a-text-normal')
                    )

                    link_el = (
                        container.select_one('h2 a') or
                        container.select_one('a.a-link-normal') or
                        container.select_one('a[href*="/dp/"]')
                    )

                    if not (title_el and link_el):
                        logger.warning(f"⚠️ Container {i+1}: Missing title or link")
                        continue

                    product_url = link_el.get("href", "")
                    if product_url.startswith("/"):
                        product_url = f"https://www.amazon.com{product_url}"

                    title_text = title_el.get_text(strip=True)
                    basic_products.append({
                        "title": title_text,
                        "url": product_url
                    })
                    logger.info(f"✅ Found product {i+1}: {title_text[:50]}...")

                # Close search browser
                await browser.close()
                await playwright.stop()

                # Concurrently fetch detailed information for all products
                logger.info(f"🔄 Fetching detailed info for {len(basic_products)} products concurrently...")
                tasks = [extract_product_details(product["url"]) for product in basic_products]
                detailed_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results and handle any exceptions
                products = []
                for i, result in enumerate(detailed_results):
                    if isinstance(result, Exception):
                        logger.error(f"❌ Error fetching details for product {i+1}: {str(result)}")
                        # Return basic info if detailed fetch failed
                        products.append({
                            **basic_products[i],
                            "price": "",
                            "rating": "",
                            "review_count": "",
                            "success": False,
                            "error": str(result)
                        })
                    else:
                        products.append(result)

                logger.info(f"✅ Completed detailed search for '{keyword}' - {len(products)} products with full details")
                return {"keyword": keyword, "products": products}

            except Exception as e:
                logger.error(f"❌ Error in detailed search: {str(e)}")
                return {"error": f"Search failed: {str(e)}"}
            finally:
                # Make sure browser is closed even if there's an error
                try:
                    await browser.close()
                    await playwright.stop()
                except:
                    pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run())

    # ---------------- Route: Get product reviews ----------------
    @app.route("/product-reviews")
    def product_reviews():
        product_url = request.args.get("url", "").strip()
        max_reviews = request.args.get("max_reviews", "10")
        try:
            max_reviews = int(max_reviews)
            if max_reviews > 50:  # Limit to prevent excessive scraping
                max_reviews = 50
        except ValueError:
            max_reviews = 10

        if not product_url:
            return jsonify({"error": "Missing product URL", "success": False}), 400

        # Basic validation for Amazon URLs
        if not ("amazon.com" in product_url and ("/dp/" in product_url or "/gp/product/" in product_url)):
            return jsonify({"error": "Invalid Amazon product URL", "success": False}), 400

        async def run():
            result = await extract_product_reviews(product_url, max_reviews)
            return result

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run())

    # ---------------- Route: Download CSV file for reviews ----------------
    @app.route("/download-csv/<filename>")
    def download_csv(filename):
        """Download CSV file with review data"""
        try:
            # Find the CSV file in exports directory
            exports_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
            filepath = os.path.join(exports_dir, filename)

            if not os.path.exists(filepath):
                return jsonify({"error": "File not found", "success": False}), 404

            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
            )
        except Exception as e:
            logger.error(f"❌ Error downloading CSV file: {str(e)}")
            return jsonify({"error": "Download failed", "success": False}), 500

    # ---------------- Route: Download Excel file for reviews ----------------
    @app.route("/download-excel/<filename>")
    def download_excel(filename):
        """Download Excel file with review data"""
        try:
            # Find the Excel file in exports directory
            exports_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
            filepath = os.path.join(exports_dir, filename)

            if not os.path.exists(filepath):
                return jsonify({"error": "File not found", "success": False}), 404

            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except Exception as e:
            logger.error(f"❌ Error downloading Excel file: {str(e)}")
            return jsonify({"error": "Download failed", "success": False}), 500

    # ---------------- Route: Search for products and get all reviews from first page ----------------
    @app.route("/search-reviews")
    def search_reviews():
        keyword = (request.args.get("q") or "").strip()
        max_products = request.args.get("max_products", "3")
        try:
            max_products = int(max_products)
            if max_products > 5:  # Limit to prevent excessive scraping
                max_products = 5
            if max_products < 1:
                max_products = 1
        except ValueError:
            max_products = 3

        if not keyword:
            return jsonify({"error": "Missing search keyword", "success": False}), 400

        async def run():
            browser, playwright, page = await get_browser(headless=True)
            try:
                # Search Amazon
                search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
                logger.info(f"🔍 Searching for: {keyword}")
                await page.goto(search_url, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                await human_delay(2000, 4000)

                # Add scrolling to load more search results
                await human_scroll(page, max_scrolls=1)

                try:
                    await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=15000)
                except:
                    html = await page.content()
                    logger.error("❌ No search results loaded")
                    return {"error": "No search results loaded", "search_term": keyword, "success": False}

                soup = BeautifulSoup(await page.content(), "html.parser")
                product_containers = (
                    soup.select('[data-component-type="s-search-result"]')
                    or soup.select('[data-asin][data-index]')
                    or soup.select('.s-result-item')
                )

                logger.info(f"🔍 Found {len(product_containers)} product containers")

                # Extract basic product info (titles and URLs)
                basic_products = []
                for i, container in enumerate(product_containers[:max_products]):
                    logger.info(f"Processing container {i+1}: {str(container)[:200]}...")

                    # Try multiple selectors for title and link
                    title_el = (
                        container.select_one('h2 a span') or
                        container.select_one('h2 span') or
                        container.select_one('.a-text-normal') or
                        container.select_one('span.a-text-normal')
                    )

                    link_el = (
                        container.select_one('h2 a') or
                        container.select_one('a.a-link-normal') or
                        container.select_one('a[href*="/dp/"]')
                    )

                    if not (title_el and link_el):
                        logger.warning(f"⚠️ Container {i+1}: Missing title or link")
                        continue

                    product_url = link_el.get("href", "")
                    if product_url.startswith("/"):
                        product_url = f"https://www.amazon.com{product_url}"

                    title_text = title_el.get_text(strip=True)
                    basic_products.append({
                        "title": title_text,
                        "url": product_url
                    })
                    logger.info(f"✅ Found product {i+1}: {title_text[:50]}...")

                # Close search browser
                await browser.close()
                await playwright.stop()

                if not basic_products:
                    return {
                        "search_term": keyword,
                        "total_products": 0,
                        "total_reviews": 0,
                        "products": [],
                        "success": False,
                        "error": "No products found"
                    }

                # Concurrently fetch reviews for all products
                logger.info(f"🔄 Fetching reviews for {len(basic_products)} products concurrently...")
                tasks = [extract_product_reviews(product["url"], float('inf')) for product in basic_products]
                review_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results and build optimized response
                products = []
                total_reviews = 0

                for i, result in enumerate(review_results):
                    if isinstance(result, Exception):
                        logger.error(f"❌ Error fetching reviews for product {i+1}: {str(result)}")
                        # Add product with no reviews
                        products.append({
                            "title": basic_products[i]["title"],
                            "url": basic_products[i]["url"],
                            "reviews_count": 0,
                            "reviews": [],
                            "success": False,
                            "error": str(result)
                        })
                    else:
                        reviews_count = result.get("total_reviews_found", 0)
                        total_reviews += reviews_count
                        products.append({
                            "title": basic_products[i]["title"],
                            "url": basic_products[i]["url"],
                            "reviews_count": reviews_count,
                            "reviews": result.get("reviews", []),
                            "success": result.get("success", False)
                        })

                logger.info(f"✅ Completed search-reviews for '{keyword}' - {len(products)} products with {total_reviews} total reviews")

                # Generate Excel file
                try:
                    excel_filepath, excel_filename = generate_excel_file(keyword, products)
                    excel_download_url = f"http://localhost:5001/download-excel/{excel_filename}"
                    logger.info(f"📊 Generated Excel file: {excel_filename}")
                except Exception as e:
                    logger.error(f"❌ Error generating Excel file: {str(e)}")
                    excel_download_url = None

                return {
                    "search_term": keyword,
                    "total_products": len(products),
                    "total_reviews": total_reviews,
                    "products": products,
                    "excel_download_url": excel_download_url,
                    "success": True
                }

            except Exception as e:
                logger.error(f"❌ Error in search-reviews: {str(e)}")
                return {
                    "search_term": keyword,
                    "error": f"Search failed: {str(e)}",
                    "success": False
                }
            finally:
                # Make sure browser is closed even if there's an error
                try:
                    await browser.close()
                    await playwright.stop()
                except:
                    pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run())

    # Serve frontend files
    @app.route('/')
    def serve_frontend():
        return send_file('../index.html')

    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_file(f'../{filename}')

    return app

app = create_app()
CORS(app)

if __name__ == "__main__":
    app.run(port=5001, debug=True)
