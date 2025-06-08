from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import time
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def setup_driver():
    """Set up the Firefox WebDriver with appropriate options."""
    firefox_options = Options()
    firefox_options.add_argument('--width=1920')
    firefox_options.add_argument('--height=1080')
    
    # Add additional preferences to improve stability
    firefox_options.set_preference('dom.webdriver.enabled', False)
    firefox_options.set_preference('useAutomationExtension', False)
    firefox_options.set_preference('privacy.trackingprotection.enabled', False)
    
    # Install and setup geckodriver
    driver_path = GeckoDriverManager().install()
    service = Service(executable_path=driver_path)
    driver = webdriver.Firefox(service=service, options=firefox_options)
    driver.set_page_load_timeout(60)
    return driver

def test_selectors():
    driver = setup_driver()
    try:
        # Test URL - ASOS men's clothing category
        url = "https://www.asos.com/men/"
        logger.info(f"Testing selectors on URL: {url}")
        
        driver.get(url)
        time.sleep(10)  # Wait for page to load
        
        # Test different selectors
        selectors = [
            # Product links
            "a[data-testid='product-link']",
            "a[data-auto-id='product-link']",
            "a[data-test-id='product-link']",
            "a[data-test='product-link']",
            "a[data-auto='product-link']",
            
            # Product containers
            "div[data-testid='product-card']",
            "div[data-auto-id='product-card']",
            "div[data-test-id='product-card']",
            "div[data-test='product-card']",
            "div[data-auto='product-card']",
            
            # Generic product selectors
            "a[href*='/prd/']",
            "div[class*='product']",
            "div[class*='Product']",
            "div[class*='item']",
            "div[class*='Item']"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                logger.info(f"Selector '{selector}' found {len(elements)} elements")
                if elements:
                    # Log the first element's HTML
                    logger.info(f"First element HTML: {elements[0].get_attribute('outerHTML')}")
            except Exception as e:
                logger.error(f"Error with selector '{selector}': {str(e)}")
        
        # Also try to get all links on the page
        all_links = driver.find_elements(By.TAG_NAME, "a")
        product_links = [link.get_attribute('href') for link in all_links if link.get_attribute('href') and '/prd/' in link.get_attribute('href')]
        logger.info(f"Found {len(product_links)} product links using tag name")
        if product_links:
            logger.info(f"Sample product link: {product_links[0]}")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    test_selectors() 