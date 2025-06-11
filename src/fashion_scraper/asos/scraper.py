"""
ASOS.com scraper implementation.
"""
from typing import Dict, List, Any
import re
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
from webdriver_manager.firefox import GeckoDriverManager
import platform
import os
from tenacity import retry, stop_after_attempt, wait_exponential
import random

from ..common.base_scraper import BaseScraper

class AsosScraper(BaseScraper):
    """ASOS.com scraper implementation."""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.asos.com",
            output_dir="data/raw/asos"
        )
        self.setup_driver()
    
    def setup_driver(self):
        """Set up the Firefox WebDriver with appropriate options."""
        self.logger.info("Setting up Firefox WebDriver")
        try:
            firefox_options = Options()
            firefox_options.add_argument('--width=1920')
            firefox_options.add_argument('--height=1080')
            firefox_options.set_preference('general.useragent.override', self.ua.random)
            
            # Add preferences to avoid detection
            firefox_options.set_preference('dom.webdriver.enabled', False)
            firefox_options.set_preference('useAutomationExtension', False)
            firefox_options.set_preference('privacy.trackingprotection.enabled', False)
            
            # Increase timeouts
            firefox_options.set_preference('dom.max_script_run_time', 30)
            firefox_options.set_preference('dom.max_chrome_script_run_time', 30)
            
            # Disable images to speed up loading
            firefox_options.set_preference('permissions.default.image', 2)
            
            # Add additional preferences to avoid detection
            firefox_options.set_preference('privacy.resistFingerprinting', True)
            firefox_options.set_preference('privacy.trackingprotection.cryptomining.enabled', False)
            firefox_options.set_preference('privacy.trackingprotection.fingerprinting.enabled', False)
            firefox_options.set_preference('privacy.trackingprotection.socialtracking.enabled', False)
            
            # Add more anti-detection measures
            firefox_options.set_preference('browser.cache.disk.enable', True)
            firefox_options.set_preference('browser.cache.memory.enable', True)
            firefox_options.set_preference('browser.cache.offline.enable', True)
            firefox_options.set_preference('network.cookie.cookieBehavior', 0)
            firefox_options.set_preference('network.http.referer.spoofSource', True)
            firefox_options.set_preference('network.proxy.type', 0)
            
            # Install and setup geckodriver
            self.logger.info("Installing geckodriver...")
            driver_path = GeckoDriverManager().install()
            self.logger.info(f"Geckodriver installed at: {driver_path}")
            
            # Make sure the geckodriver is executable
            os.chmod(driver_path, 0o755)
            
            service = Service(executable_path=driver_path)
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            
            # Set page load timeout to 60 seconds
            self.driver.set_page_load_timeout(60)
            # Set script timeout to 60 seconds
            self.driver.set_script_timeout(60)
            
            self.logger.info("Firefox WebDriver setup completed successfully")
        except Exception as e:
            self.logger.error(f"Error setting up Firefox WebDriver: {str(e)}", exc_info=True)
            raise
    
    def wait_for_page_load(self, timeout=30):
        """Wait for the page to be fully loaded."""
        try:
            # Wait for document.readyState to be 'complete'
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            
            # Wait for any AJAX requests to complete
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script('return jQuery.active') == 0
            )
            
            # Wait for any dynamic content to load
            time.sleep(5)
            
            return True
        except Exception as e:
            self.logger.warning(f"Error waiting for page load: {str(e)}")
            return False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_product_links(self, category_url: str) -> List[str]:
        """Get all product links from a category page using Selenium with retry logic."""
        self.logger.info(f"Starting to fetch product links from: {category_url}")
        product_links = []
        
        try:
            self.logger.debug("Loading category page with Selenium")
            self.driver.get(category_url)
            
            # Log page state and title
            self.logger.debug(f"Current URL: {self.driver.current_url}")
            self.logger.debug(f"Page title: {self.driver.title}")
            
            # Check if we're on the correct page
            if "asos.com" not in self.driver.current_url:
                self.logger.error(f"Redirected to unexpected URL: {self.driver.current_url}")
                raise Exception("Redirected to unexpected URL")
            
            # Wait for page to be fully loaded
            self.logger.debug("Waiting for page to be fully loaded...")
            if not self.wait_for_page_load():
                self.logger.warning("Page load wait failed, but continuing anyway")
            
            # Try to find any product-related elements first
            product_containers = []
            container_selectors = [
                'div[data-testid="product-grid"]',
                'div[data-auto-id="product-grid"]',
                'div[class*="productGrid"]',
                'div[class*="product-grid"]',
                'div[class*="product-list"]',
                'div[class*="productContainer"]',
                'div[class*="productWrapper"]',
                'div[class*="product-grid"]',
                'div[class*="product-list"]',
                'div[class*="product-container"]',
                'div[class*="product-wrapper"]',
                'div[class*="product-grid-container"]',
                'div[class*="product-list-container"]',
                'div[class*="product-grid-wrapper"]',
                'div[class*="product-list-wrapper"]'
            ]
            
            # Try to find containers with increasing timeouts
            for timeout in [10, 20, 30]:
                for selector in container_selectors:
                    try:
                        self.logger.debug(f"Trying to find containers with selector: {selector} (timeout: {timeout}s)")
                        WebDriverWait(self.driver, timeout).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if containers:
                            self.logger.debug(f"Found {len(containers)} containers with selector: {selector}")
                            product_containers.extend(containers)
                            break
                    except Exception as e:
                        self.logger.debug(f"Error finding containers with {selector}: {str(e)}")
                        continue
                
                if product_containers:
                    break
            
            # Scroll down multiple times to load more products
            self.logger.debug("Scrolling down to load more products...")
            for i in range(3):  # Scroll 3 times
                self.driver.execute_script(f"window.scrollTo(0, {(i + 1) * 1000});")
                time.sleep(3)  # Wait between scrolls
            
            # Try to find links within containers first
            if product_containers:
                self.logger.debug("Trying to find links within product containers...")
                for container in product_containers:
                    try:
                        # Try different methods to find links
                        links = []
                        
                        # Method 1: Direct link search
                        links.extend(container.find_elements(By.TAG_NAME, "a"))
                        
                        # Method 2: Search for links with specific attributes
                        links.extend(container.find_elements(By.CSS_SELECTOR, "a[href*='/prd/']"))
                        
                        # Method 3: Search for links within product cards
                        product_cards = container.find_elements(By.CSS_SELECTOR, "[class*='product']")
                        for card in product_cards:
                            links.extend(card.find_elements(By.TAG_NAME, "a"))
                        
                        # Process found links
                        for link in links:
                            try:
                                href = link.get_attribute('href')
                                if href and 'asos.com' in href and '/prd/' in href:
                                    product_links.append(href)
                                    self.logger.debug(f"Found product link in container: {href}")
                            except Exception as e:
                                self.logger.debug(f"Error getting href from link: {str(e)}")
                    except Exception as e:
                        self.logger.debug(f"Error finding links in container: {str(e)}")
            
            # If no links found in containers, try direct link search
            if not product_links:
                self.logger.debug("No links found in containers, trying direct link search...")
                link_selectors = [
                    'a[href*="/prd/"]',
                    'a[href*="asos.com"][href*="/prd/"]',
                    'a[class*="productLink"]',
                    'a[data-testid*="product"]',
                    'a[data-auto-id*="product"]'
                ]
                
                for selector in link_selectors:
                    try:
                        self.logger.debug(f"Trying to find links with selector: {selector}")
                        links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if links:
                            self.logger.debug(f"Found {len(links)} links with selector: {selector}")
                            for link in links:
                                try:
                                    href = link.get_attribute('href')
                                    if href and 'asos.com' in href and '/prd/' in href:
                                        product_links.append(href)
                                        self.logger.debug(f"Found product link: {href}")
                                except Exception as e:
                                    self.logger.debug(f"Error getting href from link: {str(e)}")
                            
                            if product_links:
                                break
                    except Exception as e:
                        self.logger.debug(f"Error finding links with {selector}: {str(e)}")
                        continue
            
            if not product_links:
                # Save page source for debugging
                debug_path = f"asos_debug_{int(time.time())}.html"
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                self.logger.error(f"Saved page source to {debug_path} for debugging.")
                
                # Fallback: Try to extract product links using BeautifulSoup
                self.logger.info("Falling back to BeautifulSoup parsing...")
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if 'asos.com' in href and '/prd/' in href:
                        product_links.append(href)
                    elif href.startswith('/prd/'):
                        product_links.append(f"https://www.asos.com{href}")
                
                if product_links:
                    self.logger.info(f"BeautifulSoup fallback found {len(product_links)} product links.")
                    return product_links
                
                # Log more debugging information before raising the exception
                self.logger.error("Could not find any product elements. Current page state:")
                self.logger.error(f"URL: {self.driver.current_url}")
                self.logger.error(f"Title: {self.driver.title}")
                self.logger.error("Available elements on page:")
                try:
                    all_elements = self.driver.find_elements(By.CSS_SELECTOR, '*')
                    self.logger.error(f"Total elements on page: {len(all_elements)}")
                    # Log some sample elements
                    for i, elem in enumerate(all_elements[:5]):
                        try:
                            self.logger.error(f"Element {i}: {elem.tag_name} - {elem.get_attribute('class')}")
                        except:
                            self.logger.error(f"Element {i}: Could not get details")
                except Exception as e:
                    self.logger.error(f"Error getting page elements: {str(e)}")
                
                raise TimeoutException("Could not find any product elements on the page")
            
            self.logger.info(f"Successfully extracted {len(product_links)} product links")
            return product_links
            
        except Exception as e:
            self.logger.error(f"Error in get_product_links: {str(e)}", exc_info=True)
            raise
    
    def scrape_product(self, product_url: str) -> Dict[str, Any]:
        """Scrape individual product details with improved error handling and anti-bot measures."""
        self.logger.info(f"Starting to scrape product: {product_url}")
        try:
            # Add random delay before loading product page
            time.sleep(random.uniform(2, 5))
            
            self.driver.get(product_url)
            
            # Wait for page load with increased timeout
            if not self.wait_for_page_load(timeout=30):
                self.logger.warning("Initial page load wait failed, but continuing anyway")
            
            # Check for bot detection
            if "unusual traffic" in self.driver.page_source.lower() or "verify you are human" in self.driver.page_source.lower():
                self.logger.error("Bot detection triggered! Saving page source for debugging...")
                debug_path = f"asos_bot_detection_{int(time.time())}.html"
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                raise Exception("Bot detection triggered")
            
            # Try to find product details using Selenium first
            try:
                product_data = {}
                
                # Try to find price (only working selector)
                try:
                    price_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-testid="current-price"]'))
                    )
                    price_text = price_element.text.strip()
                    price_text = price_text.replace('£', '').replace(',', '')
                    try:
                        product_data['price'] = float(price_text)
                    except ValueError:
                        product_data['price'] = price_text
                except Exception as e:
                    self.logger.warning(f"Failed to find price: {str(e)}")
                
                # Try to find other details using BeautifulSoup
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Try to find name
                name_element = soup.find('h1')
                if name_element:
                    product_data['name'] = name_element.text.strip()
                
                # Try to find brand
                brand_element = soup.find('a', href=lambda x: x and '/brand/' in x)
                if brand_element:
                    product_data['brand'] = brand_element.text.strip()
                
                # Try to find description
                description_element = soup.find('div', class_=lambda x: x and 'description' in x.lower())
                if description_element:
                    product_data['description'] = description_element.text.strip()
                
                # Add URL
                product_data['url'] = product_url
                
                # If we found at least the price, return the data
                if 'price' in product_data:
                    self.logger.info(f"Successfully scraped product: {product_data.get('name', 'Unknown')}")
                    return product_data
                
            except Exception as e:
                self.logger.warning(f"Selenium scraping failed: {str(e)}")
            
            # If we couldn't find any data, save the page source for debugging
            self.logger.error("Could not find any product details. Saving page source for debugging...")
            debug_path = f"asos_product_debug_{int(time.time())}.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            raise Exception("Could not find any product details")
            
        except Exception as e:
            self.logger.error(f"Error scraping product {product_url}: {str(e)}", exc_info=True)
            raise
    
    def close(self):
        """Close the web driver and clean up resources."""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def __del__(self):
        """Ensure resources are cleaned up when the object is destroyed."""
        self.close() 