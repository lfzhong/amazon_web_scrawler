import asyncio
import random
import logging
from flask import Flask, jsonify, request
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

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

    # ---------------- Route: Test product details with mock data ----------------
    @app.route("/product-details-test")
    def product_details_test():
        """Test endpoint that returns mock product data to demonstrate API structure"""
        mock_data = {
            "url": "https://www.amazon.com/dp/B08N5WRWNW",
            "title": "Apple MacBook Air (13-inch, M1 chip)",
            "price": "$999.00",
            "rating": "4.5",
            "review_count": "12,847",
            "success": True,
            "note": "This is mock data for testing. Real Amazon scraping is blocked by anti-bot measures."
        }
        return jsonify(mock_data)

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

    return app

app = create_app()

if __name__ == "__main__":
    app.run(port=5001, debug=True)
