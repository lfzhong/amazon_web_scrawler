#!/usr/bin/env python3
"""
Debug script to test review extraction
"""

import asyncio
import logging
from backend.app import create_app

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def test_review_extraction():
    """Test the review extraction function directly"""
    app = create_app()
    
    # Get the extract_product_reviews function from the app context
    with app.app_context():
        # Import the function from the app module
        from backend.app import extract_product_reviews
        
        # Test with a simple product URL
        test_url = "https://www.amazon.com/dp/B08N5WRWNW"
        
        logger.info(f"Testing review extraction for: {test_url}")
        
        try:
            result = await extract_product_reviews(test_url, max_reviews=5, max_pages=1)
            logger.info(f"Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return None

if __name__ == "__main__":
    result = asyncio.run(test_review_extraction())
    print(f"Final result: {result}")
