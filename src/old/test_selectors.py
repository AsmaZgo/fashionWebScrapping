from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import time
import logging
import os
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    """Set up the Firefox WebDriver with appropriate options."""
    firefox_options = Options()
    firefox_options.add_argument('--width=1920')
    firefox_options.add_argument('--height=1080')
    
    # Add preferences to avoid detection
    firefox_options.set_preference('dom.webdriver.enabled', False)
    firefox_options.set_preference('useAutomationExtension', False)
    firefox_options.set_preference('privacy.trackingprotection.enabled', False)
    
    # Install and setup geckodriver
    driver_path = GeckoDriverManager().install()
    os.chmod(driver_path, 0o755)
    
    service = Service(executable_path=driver_path)
    driver = webdriver.Firefox(service=service, options=firefox_options)
    driver.set_page_load_timeout(60)
    return driver

def test_selectors(url):
    """Test different selectors on a product page."""
    driver = setup_driver()
    try:
        logger.info(f"Testing selectors on: {url}")
        driver.get(url)
        time.sleep(5)  # Wait for page load
        
        # Test selectors
        selectors = {
            'name': [
                'h1[data-testid="product-title"]',
                'h1[data-auto-id="product-title"]',
                'h1[class*="product-title"]',
                'h1[class*="productTitle"]'
            ],
            'price': [
                'span[data-testid="current-price"]',
                'span[data-auto-id="current-price"]',
                'span[class*="current-price"]',
                'span[class*="price"]'
            ],
            'brand': [
                'a[data-testid="brand-link"]',
                'a[data-auto-id="brand-link"]',
                'a[class*="brand-link"]',
                'a[class*="brandLink"]'
            ],
            'description': [
                'div[data-testid="product-description"]',
                'div[data-auto-id="product-description"]',
                'div[class*="product-description"]',
                'div[class*="productDescription"]'
            ]
        }
        
        results = {}
        for field, field_selectors in selectors.items():
            results[field] = []
            logger.info(f"\nTesting {field} selectors:")
            for selector in field_selectors:
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    text = element.text.strip()
                    if text:
                        results[field].append((selector, text))
                        logger.info(f"✓ {selector}: {text[:50]}...")
                    else:
                        logger.info(f"✗ {selector}: Found but empty")
                except Exception as e:
                    logger.info(f"✗ {selector}: {str(e)}")
        
        # Test BeautifulSoup fallback
        logger.info("\nTesting BeautifulSoup fallback:")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for field, field_selectors in selectors.items():
            for selector in field_selectors:
                try:
                    element = soup.select_one(selector)
                    if element and element.text.strip():
                        logger.info(f"✓ BS4 {selector}: {element.text.strip()[:50]}...")
                    else:
                        logger.info(f"✗ BS4 {selector}: Not found or empty")
                except Exception as e:
                    logger.info(f"✗ BS4 {selector}: {str(e)}")
        
        return results
        
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test with a few different product URLs
    test_urls = [
        "https://www.asos.com/vans/vans-super-lowpro-trainers-in-brown/prd/207733452",
        "https://www.asos.com/on-running/on-cloudswift-4-running-trainers-in-grey/prd/207785711"
    ]
    
    for url in test_urls:
        results = test_selectors(url)
        print("\nResults summary:")
        for field, matches in results.items():
            if matches:
                print(f"\n{field}:")
                for selector, text in matches:
                    print(f"  {selector}: {text[:50]}...") 