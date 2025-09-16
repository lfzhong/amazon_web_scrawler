#!/usr/bin/env python3
"""
Simple test to debug review extraction
"""

import asyncio
import logging
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def human_delay(min_ms=1000, max_ms=3000):
    await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)

async def test_simple_review_extraction():
    """Test simple review extraction"""
    playwright = None
    browser = None
    page = None
    
    try:
        logger.info("Starting browser...")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Test URL
        test_url = "https://www.amazon.com/dp/B08N5WRWNW"
        logger.info(f"Navigating to: {test_url}")
        
        await page.goto(test_url, timeout=60000)
        await page.wait_for_load_state("domcontentloaded")
        await human_delay(2000, 4000)
        
        # Get page content
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        # Look for review elements
        review_containers = soup.select('li[data-hook="review"]')
        logger.info(f"Found {len(review_containers)} review containers with li[data-hook='review']")
        
        # Try other selectors
        review_containers2 = soup.select('.review')
        logger.info(f"Found {len(review_containers2)} review containers with .review")
        
        review_containers3 = soup.select('[data-hook="review"]')
        logger.info(f"Found {len(review_containers3)} review containers with [data-hook='review']")
        
        # Look for any review-related elements
        all_review_elements = soup.select('[class*="review"], [data-hook*="review"]')
        logger.info(f"Found {len(all_review_elements)} elements with 'review' in class or data-hook")
        
        # Print some sample HTML
        if all_review_elements:
            logger.info(f"Sample review element: {str(all_review_elements[0])[:200]}...")
        
        # Check if we're on the right page
        title = soup.select_one('title')
        if title:
            logger.info(f"Page title: {title.get_text()}")
        
        # Check for common Amazon elements
        product_title = soup.select_one('#productTitle')
        if product_title:
            logger.info(f"Product title: {product_title.get_text()[:100]}...")
        
        # Check current URL
        current_url = page.url
        logger.info(f"Current URL: {current_url}")
        
        # Check for any error messages or captcha
        error_elements = soup.select('.a-alert-error, .a-alert-warning, #captcha, .captcha')
        if error_elements:
            logger.info(f"Found error/captcha elements: {len(error_elements)}")
            for elem in error_elements[:3]:
                logger.info(f"Error element: {elem.get_text()[:100]}...")
        
        # Check for sign-in prompts
        signin_elements = soup.select('[data-action="sign-in"], .a-button-signin, #nav-link-accountList')
        if signin_elements:
            logger.info(f"Found sign-in elements: {len(signin_elements)}")
        
        # Save page content for debugging
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("Saved page content to debug_page.html")
        
        return {
            "review_containers_li": len(review_containers),
            "review_containers_class": len(review_containers2),
            "review_containers_data_hook": len(review_containers3),
            "all_review_elements": len(all_review_elements),
            "page_title": title.get_text() if title else "No title",
            "product_title": product_title.get_text()[:100] if product_title else "No product title",
            "current_url": current_url,
            "error_elements": len(error_elements),
            "signin_elements": len(signin_elements)
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {"error": str(e)}
    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()

if __name__ == "__main__":
    result = asyncio.run(test_simple_review_extraction())
    print(f"Test result: {result}")
