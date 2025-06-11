"""
Base scraper class that defines common functionality for all fashion scrapers.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging
from fake_useragent import UserAgent

class BaseScraper(ABC):
    """Base class for all fashion scrapers."""
    
    def __init__(self, base_url: str, output_dir: str):
        """
        Initialize the base scraper.
        
        Args:
            base_url: The base URL of the website to scrape
            output_dir: Directory to save scraped data
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ua = UserAgent()
    
    @abstractmethod
    def setup_driver(self):
        """Set up the web driver for the specific scraper."""
        pass
    
    @abstractmethod
    def get_product_links(self, category_url: str) -> List[str]:
        """Get all product links from a category page."""
        pass
    
    @abstractmethod
    def scrape_product(self, product_url: str) -> Dict[str, Any]:
        """Scrape individual product details."""
        pass
    
    @abstractmethod
    def close(self):
        """Close the web driver and clean up resources."""
        pass
    
    def __del__(self):
        """Ensure resources are cleaned up when the object is destroyed."""
        self.close() 