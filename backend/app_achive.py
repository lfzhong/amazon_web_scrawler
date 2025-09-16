import re
import asyncio
import random
import logging
import os
from datetime import datetime
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
    # Desktop
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) "
    "Gecko/20100101 Firefox/123.0",
    # Mobile
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36"
]

def create_app() -> Flask:
    app = Flask(__name__)

    # ---------------- Debug functions ----------------
    async def debug_save_page(page, step_name, keyword=""):
        """Save page content and screenshot for debugging"""
        try:
            debug_dir = f"debug_pages/{keyword.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(debug_dir, exist_ok=True)
            
            # Save HTML
            html_content = await page.content()
            with open(f"{debug_dir}/{step_name}.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Save screenshot
            await page.screenshot(path=f"{debug_dir}/{step_name}.png", full_page=True)
            
            logger.info(f"🔍 Debug: Saved {step_name} - HTML and screenshot to {debug_dir}/")
            
            # Log page title and URL
            title = await page.title()
            url = page.url
            logger.info(f"📄 Page: {title} | URL: {url}")
            
        except Exception as e:
            logger.warning(f"⚠️ Debug save failed for {step_name}: {e}")

    async def debug_log_selectors(page, selectors, step_name):
        """Debug function to check if selectors are found"""
        logger.info(f"🔍 Debug: Checking selectors for {step_name}")
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                logger.info(f"   Selector '{selector}': Found {len(elements)} elements")
                if len(elements) > 0:
                    # Log first element's text content (truncated)
                    text = await elements[0].text_content()
                    logger.info(f"   First element text: {text[:100]}{'...' if len(text) > 100 else ''}")
            except Exception as e:
                logger.warning(f"   Selector '{selector}': Error - {e}")

    # ---------------- Helper: Human-like delay ----------------
    async def human_delay(min_ms=1000, max_ms=3000):
        await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)
    
    # ---------------- Helper: Random mouse movement ----------------
    async def random_mouse_movement(page):
        try:
            await page.mouse.move(
                random.randint(100, 800), 
                random.randint(100, 600)
            )
            await asyncio.sleep(random.uniform(0.1, 0.3))
        except:
            pass  

    # ---------------- Helper: Start browser with rotation ----------------
    async def get_browser(headless=True):
        ua = random.choice(USER_AGENTS)
        viewport = {
            "width": random.randint(1280, 1920),
            "height": random.randint(720, 1080),
        }
        scale_factor = random.choice([1, 1.25, 1.5, 2])

        logger.info(f"🌐 Using UA: {ua[:60]}..., viewport={viewport}, scale={scale_factor}")

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
                "--disable-features=TranslateUI",
                "--disable-features=VizDisplayCompositor",
            ]
        )
        context = await browser.new_context(
            user_agent=ua,
            locale="en-US",
            timezone_id="America/New_York",
            viewport=viewport,
            device_scale_factor=scale_factor
        )
        page = await context.new_page()
        return browser, playwright, page

    # ---------------- Route: Top products with info + reviews ----------------
    @app.route("/top-products")
    def top_products():
        keyword = (request.args.get("q") or "").strip()
        if not keyword:
            return jsonify({"error": "Missing search keyword"}), 400

        async def run():
            browser, playwright, page = await get_browser(headless=True)
            try:
                # Step 1. Search Amazon
                search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
                logger.info(f"🔍 Searching for: {keyword}")
                await page.goto(search_url, timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                await human_delay(2000, 4000)
                await random_mouse_movement(page)

                # Debug: Save search page
                await debug_save_page(page, "01_search_page", keyword)
                
                # Debug: Check for common selectors
                search_selectors = [
                    '[data-component-type="s-search-result"]',
                    '[data-asin][data-index]',
                    '.s-result-item',
                    '#search',
                    '.s-search-results',
                    '.s-main-slot'
                ]
                await debug_log_selectors(page, search_selectors, "search_results")

                try:
                    await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=15000)
                except:
                    # Debug: Save the page that failed to load results
                    await debug_save_page(page, "02_no_results_page", keyword)
                    html = await page.content()
                    logger.error("❌ No search results (maybe login wall)")
                    logger.warning(html[:1000])
                    return {"error": "No search results loaded (maybe login wall)"}

                soup = BeautifulSoup(await page.content(), "html.parser")
                product_containers = (
                    soup.select('[data-component-type="s-search-result"]')
                    or soup.select('[data-asin][data-index]')
                    or soup.select('.s-result-item')
                )

                logger.info(f"🔍 Found {len(product_containers)} product containers")
                
                # Debug: Log first few containers
                for i, container in enumerate(product_containers[:3]):
                    logger.info(f"   Container {i+1}: {str(container)[:200]}...")

                products = []
                for container in product_containers[:3]:
                    title_el = container.select_one('h2 a span')
                    link_el = container.select_one('h2 a')
                    if not (title_el and link_el):
                        logger.warning(f"⚠️ Skipping container - missing title or link: {str(container)[:100]}...")
                        continue
                    product_url = link_el.get("href", "")
                    if product_url.startswith("/"):
                        product_url = f"https://www.amazon.com{product_url}"
                    products.append({
                        "title": title_el.get_text(strip=True),
                        "url": product_url
                    })
                    logger.info(f"✅ Found product: {title_el.get_text(strip=True)[:50]}...")

                results = []
                # Step 2. Product info + reviews
                for i, product in enumerate(products):
                    logger.info(f"🔍 Processing product {i+1}/{len(products)}: {product['title'][:50]}...")
                    
                    asin_match = re.search(r"/dp/([A-Z0-9]{10})", product["url"])
                    if not asin_match:
                        logger.warning(f"⚠️ No ASIN found in URL: {product['url']}")
                        continue
                    asin = asin_match.group(1)
                    logger.info(f"📦 ASIN: {asin}")

                    await page.goto(product["url"], timeout=60000)
                    await page.wait_for_load_state("domcontentloaded")
                    await human_delay(2000, 4000)

                    # Debug: Save product page
                    await debug_save_page(page, f"03_product_{i+1}_page", keyword)

                    soup = BeautifulSoup(await page.content(), "html.parser")
                    price_el = soup.select_one("span.a-price span.a-offscreen")
                    rating_el = soup.select_one("span.a-icon-alt")
                    total_reviews_el = soup.select_one("#acrCustomerReviewText")
                    
                    # Debug: Log product info elements
                    logger.info(f"   Price element: {price_el.get_text(strip=True) if price_el else 'Not found'}")
                    logger.info(f"   Rating element: {rating_el.get_text(strip=True) if rating_el else 'Not found'}")
                    logger.info(f"   Review count element: {total_reviews_el.get_text(strip=True) if total_reviews_el else 'Not found'}")

                    product_info = {
                        "price": price_el.get_text(strip=True) if price_el else "",
                        "avg_rating": rating_el.get_text(strip=True) if rating_el else "",
                        "review_count": total_reviews_el.get_text(strip=True) if total_reviews_el else ""
                    }

                    # Go to reviews
                    review_url = f"https://www.amazon.com/product-reviews/{asin}/"
                    try:
                        ratings_link = await page.query_selector("a#acrCustomerReviewLink")
                        if ratings_link:
                            logger.info(f"   🔗 Clicking on reviews link")
                            await ratings_link.click()
                            await page.wait_for_load_state("domcontentloaded")
                            await human_delay(2000, 3000)
                            review_url = page.url
                        else:
                            logger.info(f"   🔗 Reviews link not found, navigating directly")
                            await page.goto(review_url, timeout=60000)
                            await page.wait_for_load_state("domcontentloaded")
                            await human_delay(2000, 3000)
                    except Exception as e:
                        logger.warning(f"   ⚠️ Error navigating to reviews: {e}")
                        await page.goto(review_url, timeout=60000)
                        await page.wait_for_load_state("domcontentloaded")
                        await human_delay(2000, 3000)

                    # Debug: Save reviews page
                    await debug_save_page(page, f"04_reviews_{i+1}_page", keyword)

                    # Scrape reviews
                    soup = BeautifulSoup(await page.content(), "html.parser")
                    review_blocks = soup.select('li[data-hook="review"]')
                    logger.info(f"   📝 Found {len(review_blocks)} review blocks")
                    
                    # Debug: Check review selectors
                    review_selectors = [
                        'li[data-hook="review"]',
                        '.review',
                        '[data-hook="review"]',
                        '.a-section.review'
                    ]
                    await debug_log_selectors(page, review_selectors, f"reviews_{i+1}")
                    
                    top_reviews = []
                    for block in review_blocks[:5]:
                        author_el = block.select_one('span.a-profile-name')
                        rating_el = block.select_one('i[data-hook="review-star-rating"] span')
                        title_el = block.select_one('a[data-hook="review-title"] span')
                        content_el = block.select_one('span[data-hook="review-body"] span')
                        date_el = block.select_one('span[data-hook="review-date"]')
                        verified_el = block.select_one('span[data-hook="avp-badge"]')

                        rating_text = rating_el.get_text(strip=True) if rating_el else ""
                        rating_match = re.search(r"([\d.]+)", rating_text)
                        rating = rating_match.group(1) if rating_match else ""

                        top_reviews.append({
                            "author": author_el.get_text(strip=True) if author_el else "",
                            "rating": rating,
                            "title": title_el.get_text(strip=True) if title_el else "",
                            "content": content_el.get_text(" ", strip=True) if content_el else "",
                            "date": date_el.get_text(strip=True) if date_el else "",
                            "verified": bool(verified_el),
                        })

                    results.append({
                        "product_url": product["url"],
                        "product_info": product_info,
                        "review_url": review_url,
                        "top_reviews": top_reviews
                    })

                return {"keyword": keyword, "products": results}

            finally:
                await browser.close()
                await playwright.stop()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run())

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)
