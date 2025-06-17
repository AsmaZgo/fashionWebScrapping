import argparse
import json
from pathlib import Path
import logging
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import platform
import time
from selenium.common.exceptions import WebDriverException
from urllib3.exceptions import NewConnectionError
import backoff

from fashion_scraper.asos.scraper import AsosScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_driver():
    """Set up and return a Firefox WebDriver."""
    # Set up Firefox options
    firefox_options = Options()
    firefox_options.add_argument('--disable-blink-features=AutomationControlled')
    firefox_options.add_argument('--window-size=1920,1080')
    firefox_options.set_preference('general.useragent.override', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    # Add additional preferences
    firefox_options.set_preference('dom.webdriver.enabled', False)
    firefox_options.set_preference('useAutomationExtension', False)
    
    # Set up GeckoDriver
    service = Service(GeckoDriverManager().install())
    
    return webdriver.Firefox(
        service=service,
        options=firefox_options
    )

@backoff.on_exception(backoff.expo, 
                     (WebDriverException, NewConnectionError),
                     max_tries=3,
                     giveup=lambda e: "Failed to establish a new connection" not in str(e))
def scrape_with_retry(scraper, url):
    """Scrape a product with retry logic."""
    return scraper.scrape_product(url)

def main():
    parser = argparse.ArgumentParser(description="Scrape a single ASOS product")
    parser.add_argument('--url', required=True, help="URL of the product to scrape")
    parser.add_argument('--output', required=True, help="Directory to save the scraped data")
    parser.add_argument('--debug', action='store_true', help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    driver = None
    try:
        # Initialize the driver
        driver = setup_driver()
        
        # Initialize the scraper
        scraper = AsosScraper()
        scraper.driver = driver
        
        # Scrape the product
        logger.info(f"Scraping product: {args.url}")
        
        # Add a longer delay before scraping to let the page load properly
        time.sleep(5)
        
        try:
            # Use retry logic for scraping
            product_data = scrape_with_retry(scraper, args.url)
            
            # Create output directory
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the data
            output_file = output_dir / f"product_{product_data.get('product_id', 'unknown')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(product_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved product data to: {output_file}")
            
            # Print the data for inspection
            print("\nScraped Product Data:")
            print(json.dumps(product_data, indent=2))
            
        except Exception as e:
            logger.error(f"Error scraping product: {str(e)}")
            # Save partial data if available
            if 'product_data' in locals():
                output_dir = Path(args.output)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / f"product_{product_data.get('product_id', 'unknown')}_partial.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(product_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved partial product data to: {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")

if __name__ == "__main__":
    main() 