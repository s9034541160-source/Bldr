import asyncio
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_source(url, selector):
    """Test if we can access a source and find documents"""
    try:
        logger.info(f"Testing source: {url}")
        
        # Create HTTP client that follows redirects and ignores SSL errors
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
            # Get the main page
            response = await client.get(url, headers={"User-Agent": "Bldr-Bot/1.0 (for norms)"})
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find document links
            links = soup.select(selector)
            
            logger.info(f"Found {len(links)} links")
            
            # Show first few links
            for i, link in enumerate(links[:10]):
                href = link.get('href')
                text = link.get_text(strip=True)
                logger.info(f"Link {i+1}: {href} - {text}")
                
    except Exception as e:
        logger.error(f"Error testing source: {str(e)}")

async def main():
    # Test defsmeta.ru with broader selector
    await test_source("https://www.defsmeta.ru/", "a[href]")
    
    print("\n" + "="*50 + "\n")
    
    # Test defsmeta.ru specific pages based on search results
    await test_source("https://www.defsmeta.ru/defsmeta6/help/main_plan_budget_in.php", "a[href*='gesn']")
    
    print("\n" + "="*50 + "\n")
    
    # Test stroyinf.ru
    await test_source("https://files.stroyinf.ru/", "a[href$='.pdf'], a[href$='.htm']")

if __name__ == "__main__":
    asyncio.run(main())