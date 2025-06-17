import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
from pathlib import Path
import sys
import platform

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from fashion_scraper.asos.scraper import AsosScraper

class TestASOSReviews(unittest.TestCase):
    def setUp(self):
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Set up ChromeDriver based on OS
        if platform.system() == 'Darwin':  # macOS
            chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            service = Service()
        else:
            service = Service(ChromeDriverManager().install())
        
        # Initialize the driver
        self.driver = webdriver.Chrome(
            service=service,
            options=chrome_options
        )
        
        # Initialize the scraper
        self.scraper = AsosScraper()
        self.scraper.driver = self.driver  # Set the driver after initialization
        
        # Test product URL
        self.test_url = "https://www.asos.com/asos-design/asos-design-waterproof-stainless-steel-pack-of-2-necklaces-with-sealife-details-in-gold-tone/prd/208476670#colourWayId-208476686"

    def test_reviews_scraping(self):
        """Test if reviews are scraped correctly."""
        # Scrape the product
        product_data = self.scraper.scrape_product(self.test_url)
        
        # Print the scraped data for inspection
        print("\nScraped Product Data:")
        print(json.dumps(product_data, indent=2))
        
        # Test overall rating
        self.assertIn('overall_rating', product_data, "Overall rating should be present")
        self.assertIsInstance(product_data['overall_rating'], (float, type(None)), 
                            "Overall rating should be a float or None")
        
        # Test total reviews
        self.assertIn('total_reviews', product_data, "Total reviews count should be present")
        self.assertIsInstance(product_data['total_reviews'], (int, type(None)), 
                            "Total reviews should be an integer or None")
        
        # Test all_reviews
        self.assertIn('all_reviews', product_data, "All reviews should be present")
        self.assertIsInstance(product_data['all_reviews'], list, 
                            "All reviews should be a list")
        
        # If there are reviews, test their structure
        if product_data['all_reviews']:
            review = product_data['all_reviews'][0]
            self.assertIn('rating', review, "Review should have a rating")
            self.assertIn('date', review, "Review should have a date")
            self.assertIn('status', review, "Review should have a status")
            self.assertIn('title', review, "Review should have a title")
            self.assertIn('text', review, "Review should have text")
            
            # Test rating format
            self.assertIsInstance(review['rating'], (float, type(None)), 
                                "Review rating should be a float or None")
            
            # Test date format
            self.assertIsInstance(review['date'], str, 
                                "Review date should be a string")
            
            # Test status format
            self.assertIsInstance(review['status'], str, 
                                "Review status should be a string")
            
            # Test title format
            self.assertIsInstance(review['title'], str, 
                                "Review title should be a string")
            
            # Test text format
            self.assertIsInstance(review['text'], str, 
                                "Review text should be a string")

    def tearDown(self):
        """Clean up after the test."""
        self.driver.quit()

if __name__ == '__main__':
    unittest.main() 