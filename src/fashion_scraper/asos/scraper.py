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
            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda driver: driver.execute_script('return jQuery.active') == 0
                )
            except:
                self.logger.debug("jQuery.active check failed, continuing anyway")
            
            # Wait for any dynamic content to load
            time.sleep(random.uniform(3, 5))
            
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
            
            # Scroll down multiple times to load more products
            self.logger.debug("Scrolling down to load more products...")
            for i in range(5):  # Scroll 5 times
                self.driver.execute_script(f"window.scrollTo(0, {(i + 1) * 1000});")
                time.sleep(random.uniform(2, 4))  # Random wait between scrolls
            
            # Try to find product links using multiple methods
            link_selectors = [
                'a[href*="/prd/"]',
                'a[href*="asos.com"][href*="/prd/"]',
                'a[class*="productLink"]',
                'a[data-testid*="product"]',
                'a[data-auto-id*="product"]',
                'a[href*="product"]',
                'a[class*="product"]',
                'a[data-testid="product-link"]',
                'a[data-auto-id="product-link"]',
                'a[class*="product-card"]',
                'a[class*="product-tile"]',
                'a[class*="product-item"]'
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
            
            # Remove duplicates while preserving order
            product_links = list(dict.fromkeys(product_links))
            self.logger.info(f"Successfully extracted {len(product_links)} unique product links")
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
            
            try:
                product_data = {}
                # Price
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
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                # Name
                name_element = soup.find('h1')
                if name_element:
                    product_data['name'] = name_element.text.strip()
                # Brand
                brand_element = soup.find('a', href=lambda x: x and '/brand/' in x)
                if brand_element:
                    product_data['brand'] = brand_element.text.strip()
                # Brand Details
                brand_details = None
                brand_section = soup.find('div', {'data-testid': 'productDescriptionBrand'})
                if brand_section:
                    brand_content = brand_section.find('div', class_='F_yfF')
                    if brand_content:
                        brand_details = brand_content.get_text(strip=True)
                product_data['brand_details'] = brand_details

                # About Me
                about_me = None
                about_section = soup.find('div', {'data-testid': 'productDescriptionAboutMe'})
                if about_section:
                    about_content = about_section.find('div', class_='F_yfF')
                    if about_content:
                        about_me = about_content.get_text(strip=True)
                product_data['about_me'] = about_me

                # Saved Items Count
                saved_count = None
                saved_div = soup.find('div', {'class': 'ii5iT'})
                if saved_div:
                    count_span = saved_div.find('span', {'class': 'BFMOG'})
                    if count_span:
                        try:
                            saved_count = int(count_span.text.strip())
                        except ValueError:
                            saved_count = None
                product_data['saved_count'] = saved_count

                # Ratings and Reviews
                ratings_data = {}
                reviews_section = soup.find('div', {'data-testid': 'reviews-and-product-rating'})
                if reviews_section:
                    # Overall rating
                    rating_div = reviews_section.find('div', {'data-testid': 'overall-rating'})
                    if rating_div:
                        try:
                            ratings_data['overall_rating'] = float(rating_div.text.strip())
                        except ValueError:
                            ratings_data['overall_rating'] = None

                    # Total reviews
                    reviews_div = reviews_section.find('div', {'data-testid': 'total-reviews'})
                    if reviews_div:
                        reviews_text = reviews_div.text.strip()
                        try:
                            ratings_data['total_reviews'] = int(reviews_text.strip('()').split()[0])
                        except (ValueError, IndexError):
                            ratings_data['total_reviews'] = None

                    # Recommendation percentage
                    recommend_p = soup.find('p', {'class': 'NeBNz'})
                    if recommend_p:
                        recommend_text = recommend_p.text.strip()
                        try:
                            ratings_data['recommendation_percentage'] = int(recommend_text.split('%')[0])
                        except (ValueError, IndexError):
                            ratings_data['recommendation_percentage'] = None

                    # Fit and Quality ratings
                    rating_bars = soup.find_all('div', {'data-testid': 'ratingBar'})
                    if len(rating_bars) >= 2:
                        # Fit rating
                        fit_bar = rating_bars[0]
                        fit_percentage = fit_bar.find('div', {'class': 'qKPxB'})
                        if fit_percentage:
                            try:
                                ratings_data['fit_rating'] = int(fit_percentage['style'].split(':')[1].strip('%;'))
                            except (ValueError, KeyError):
                                ratings_data['fit_rating'] = None

                        # Quality rating
                        quality_bar = rating_bars[1]
                        quality_percentage = quality_bar.find('div', {'class': 'qKPxB'})
                        if quality_percentage:
                            try:
                                ratings_data['quality_rating'] = int(quality_percentage['style'].split(':')[1].strip('%;'))
                            except (ValueError, KeyError):
                                ratings_data['quality_rating'] = None

                product_data['ratings'] = ratings_data

                # Most Recent Review
                recent_review = {}
                review_section = soup.find('section', {'aria-label': lambda x: x and 'Review' in x})
                if review_section:
                    # Review rating
                    rating_p = review_section.find('p', {'class': 'seSWD'})
                    if rating_p:
                        try:
                            recent_review['rating'] = float(rating_p.text.strip().split()[0])
                        except (ValueError, IndexError):
                            recent_review['rating'] = None

                    # Review date
                    date_span = review_section.find('span', {'class': 'L0xqb'})
                    if date_span:
                        recent_review['date'] = date_span.text.strip()

                    # Reviewer status
                    status_p = review_section.find('p', {'class': 'm0ehn'})
                    if status_p:
                        recent_review['status'] = status_p.text.strip()

                    # Review title
                    title_h4 = review_section.find('h4', {'class': 'DBTNB'})
                    if title_h4:
                        recent_review['title'] = title_h4.text.strip()

                    # Review text
                    review_button = review_section.find('button', {'data-testid': 'reviewsReadMore'})
                    if review_button:
                        recent_review['text'] = review_button.text.strip()

                product_data['recent_review'] = recent_review

                # Get all reviews
                all_reviews = []
                try:
                    # Handle cookie consent banner if present
                    try:
                        cookie_button = self.driver.find_element(By.ID, "onetrust-accept-btn-handler")
                        if cookie_button:
                            cookie_button.click()
                            time.sleep(1)  # Wait for banner to disappear
                    except:
                        pass  # No cookie banner found, continue

                    # Wait for reviews section to be present
                    try:
                        # First check if there are any reviews using the correct selector
                        reviews_section = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="reviewsSection"]'))
                        )
                        
                        # Get overall rating and review count first
                        try:
                            rating_div = reviews_section.find_element(By.CSS_SELECTOR, 'div[data-testid="overall-rating"]')
                            if rating_div:
                                try:
                                    product_data['overall_rating'] = float(rating_div.text.strip())
                                except (ValueError, TypeError):
                                    product_data['overall_rating'] = None

                            reviews_div = reviews_section.find_element(By.CSS_SELECTOR, 'div[data-testid="total-reviews"]')
                            if reviews_div:
                                try:
                                    # Extract number from text like "(4 Reviews)"
                                    reviews_text = reviews_div.text.strip()
                                    product_data['total_reviews'] = int(reviews_text.strip('()').split()[0])
                                except (ValueError, TypeError):
                                    product_data['total_reviews'] = None
                        except Exception as e:
                            self.logger.warning(f"Error getting overall rating: {str(e)}")

                        # Try to find and click the View All Reviews button
                        try:
                            view_all_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="reviewsViewAll"]'))
                            )
                            
                            # Scroll to the button to ensure it's in view
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", view_all_button)
                            time.sleep(1)  # Wait for scroll to complete
                            
                            # Try to click using JavaScript if regular click fails
                            try:
                                view_all_button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", view_all_button)
                            
                            # Wait for reviews to load
                            time.sleep(2)  # Give time for reviews to load
                        except Exception as e:
                            self.logger.warning(f"Could not click View All Reviews button: {str(e)}")
                        
                        # Get the updated page source
                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        
                        # Find all review sections using the correct class
                        review_sections = soup.find_all('section', {'class': 'x5rH4'})
                        
                        # Process each review section
                        for review_section in review_sections:
                            review_data = {}
                            
                            # Review rating
                            rating_p = review_section.find('p', {'class': 'seSWD'})
                            if rating_p:
                                try:
                                    review_data['rating'] = float(rating_p.text.strip().split()[0])
                                except (ValueError, IndexError):
                                    review_data['rating'] = None

                            # Review date
                            date_span = review_section.find('span', {'class': 'L0xqb'})
                            if date_span:
                                review_data['date'] = date_span.text.strip()

                            # Reviewer status
                            status_p = review_section.find('p', {'class': 'm0ehn'})
                            if status_p:
                                review_data['status'] = status_p.text.strip()

                            # Review title
                            title_h4 = review_section.find('h4', {'class': 'DBTNB'})
                            if title_h4:
                                review_data['title'] = title_h4.text.strip()

                            # Review text
                            review_button = review_section.find('button', {'data-testid': 'reviewsReadMore'})
                            if review_button:
                                # Get the full text from the button's aria-label
                                full_text = review_button.get('aria-label', '')
                                if full_text:
                                    # Remove the "Read More" part
                                    review_data['text'] = full_text.replace('... Read More', '')
                                else:
                                    # Fall back to button text
                                    review_data['text'] = review_button.text.strip().replace('Read More', '')

                            if review_data:  # Only add if we found some data
                                all_reviews.append(review_data)
                                
                    except Exception as e:
                        self.logger.warning(f"No reviews section found: {str(e)}")
                                
                except Exception as e:
                    self.logger.warning(f"Error getting all reviews: {str(e)}")

                product_data['all_reviews'] = all_reviews

                # Scrape "You Might Also Like" section
                try:
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    might_like_section = soup.find('section', {'data-testid': 'mightLikeGrid'})
                    might_like_products = []
                    if might_like_section:
                        self.logger.info("Found 'You Might Also Like' section")
                        for li in might_like_section.select('ul.G4N4r > li.SuUpL'):
                            product = {}
                            a_tag = li.find('a', class_='Usg4d')
                            if a_tag:
                                product['url'] = a_tag['href']
                                if a_tag.has_attr('aria-label'):
                                    product['title'] = a_tag['aria-label'].split('. £')[0]
                                else:
                                    product['title'] = a_tag.get('title', '')
                            img_tag = li.find('img', class_='gb1Ne')
                            if img_tag:
                                product['image'] = img_tag['src']
                            price_span = li.find('span', {'data-testid': 'current-price'})
                            if price_span:
                                product['price'] = price_span.text.strip()
                            if product:
                                might_like_products.append(product)
                        self.logger.info(f"Found {len(might_like_products)} products in 'You Might Also Like' section")
                    else:
                        self.logger.warning("Could not find 'You Might Also Like' section")
                    product_data['people_also_like'] = might_like_products

                    # Scrape "People Also Bought" section
                    try:
                        people_bought_section = soup.find('section', {'data-testid': 'carousel'})
                        people_bought_products = []
                        if people_bought_section:
                            self.logger.info("Found 'People Also Bought' section")
                            for li in people_bought_section.select('ul.styles-module_list__1fExD > li.styles-module_listItem__B41uo'):
                                product = {}
                                a_tag = li.find('a', class_='Usg4d')
                                if a_tag:
                                    product['url'] = a_tag['href']
                                    if a_tag.has_attr('aria-label'):
                                        product['title'] = a_tag['aria-label'].split('. £')[0]
                                    else:
                                        product['title'] = a_tag.get('title', '')
                                img_tag = li.find('img', class_='gb1Ne')
                                if img_tag:
                                    product['image'] = img_tag['src']
                                price_span = li.find('span', {'data-testid': 'current-price'})
                                if price_span:
                                    product['price'] = price_span.text.strip()
                                if product:
                                    people_bought_products.append(product)
                            self.logger.info(f"Found {len(people_bought_products)} products in 'People Also Bought' section")
                        else:
                            self.logger.warning("Could not find 'People Also Bought' section")
                        product_data['people_also_bought'] = people_bought_products
                    except Exception as e:
                        self.logger.warning(f"Error scraping 'People Also Bought': {str(e)}")

                except Exception as e:
                    self.logger.warning(f"Error scraping 'You Might Also Like': {str(e)}")

                # Description
                description_element = soup.find('div', class_=lambda x: x and 'description' in x.lower())
                if description_element:
                    product_data['description'] = description_element.text.strip()
                # Color
                color = None
                color_div = soup.find('div', {'data-testid': 'productColour'})
                if color_div:
                    color_p = color_div.find('p', class_='aKxaq')
                    if color_p:
                        color = color_p.text.strip()
                product_data['colors'] = [color] if color else []
                # Product Details (bullets)
                details = []
                # Look for the accordion item with Product Details
                details_section = soup.find('span', class_='accordion-item-module_titleText__rWfj1', string='Product Details')
                if details_section:
                    # Find the next div with class F_yfF that contains the details
                    details_div = details_section.find_next('div', class_='F_yfF')
                    if details_div:
                        # Get all list items
                        list_items = details_div.find_all('li')
                        if list_items:
                            details = [li.get_text(strip=True) for li in list_items if li.get_text(strip=True)]
                        else:
                            # If no list items, get all text content
                            text = details_div.get_text(strip=True)
                            if text:
                                details = [text]
                product_data['details'] = details
                # Product Code
                code = None
                code_p = soup.find('p', class_='Jk9Oz')
                if code_p:
                    code_text = code_p.text.strip()
                    code_match = re.search(r'Product Code:\s*(\d+)', code_text)
                    if code_match:
                        code = code_match.group(1)
                product_data['product_code'] = code
                # Images
                images = []
                image_elements = soup.find_all('img', {'class': lambda x: x and 'product-image' in x.lower()})
                for img in image_elements:
                    # Get the full resolution image URL from data attributes
                    full_res_url = img.get('src', '')
                    if not full_res_url:
                        full_res_url = img.get('data-src', '')
                    if not full_res_url:
                        full_res_url = img.get('data-full-image', '')
                    
                    # If we found a URL, clean it up
                    if full_res_url:
                        # Remove any size parameters
                        full_res_url = full_res_url.split('?')[0]
                        # Add full resolution parameters
                        full_res_url = f"{full_res_url}?$n_960w$&wid=951&fit=constrain"
                        images.append(full_res_url)
                
                product_data['images'] = images
                # Add URL
                product_data['url'] = product_url
                if 'price' in product_data:
                    self.logger.info(f"Successfully scraped product: {product_data.get('name', 'Unknown')}")
                    return product_data
            except Exception as e:
                self.logger.warning(f"Selenium scraping failed: {str(e)}")
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