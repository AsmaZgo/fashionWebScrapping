from abc import ABC, abstractmethod
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd
from pathlib import Path
import logging
from tqdm import tqdm

class BaseScraper(ABC):
    def __init__(self, base_url: str, output_dir: str = "data/raw"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ua = UserAgent()
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _get_headers(self) -> Dict[str, str]:
        """Generate random headers for requests."""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with error handling and rate limiting."""
        try:
            self.logger.debug(f"Making {method} request to {url}")
            time.sleep(2)  # Rate limiting
            response = self.session.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                **kwargs
            )
            response.raise_for_status()
            self.logger.debug(f"Successfully received response from {url}")
            return response
        except requests.RequestException as e:
            self.logger.error(f"Error making request to {url}: {str(e)}")
            return None

    def _parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup."""
        return BeautifulSoup(html_content, 'lxml')

    @abstractmethod
    def get_product_links(self, category_url: str) -> List[str]:
        """Get all product links from a category page."""
        pass

    @abstractmethod
    def scrape_product(self, product_url: str) -> Dict:
        """Scrape individual product details."""
        pass

    @abstractmethod
    def scrape_reviews(self, product_url: str) -> List[Dict]:
        """Scrape product reviews."""
        pass

    def save_to_json(self, data: Dict, filename: str):
        """Save scraped data to JSON file."""
        filepath = self.output_dir / f"{filename}.json"
        self.logger.info(f"Saving data to {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_to_csv(self, data: List[Dict], filename: str):
        """Save scraped data to CSV file."""
        filepath = self.output_dir / f"{filename}.csv"
        self.logger.info(f"Saving data to {filepath}")
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8')

    def scrape_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        """Scrape all products from a category page."""
        self.logger.info(f"Starting to scrape category: {category_url}")
        products = []
        
        try:
            # Get product links
            product_links = self.get_product_links(category_url)
            
            # Limit the number of products to scrape
            product_links = product_links[:max_products]
            
            # Get details for each product
            for link in product_links:
                try:
                    product_details = self.scrape_product(link)
                    if product_details:
                        products.append(product_details)
                        self.logger.info(f"Successfully scraped product: {product_details['name']}")
                except Exception as e:
                    self.logger.error(f"Error scraping product {link}: {str(e)}")
                    continue
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error scraping category: {str(e)}")
            return []

    def run(self, category_urls: List[str]):
        """Run the scraper for multiple categories."""
        self.logger.info(f"Starting scraper for {len(category_urls)} categories")
        
        for i, category_url in enumerate(category_urls, 1):
            self.logger.info(f"Processing category {i}/{len(category_urls)}: {category_url}")
            self.scrape_category(category_url)
            
        self.logger.info("Completed all categories") 