"""
Unit tests for the ASOS scraper.
"""
import unittest
from unittest.mock import Mock, patch
from ..asos.scraper import AsosScraper

class TestAsosScraper(unittest.TestCase):
    """Test cases for the ASOS scraper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = AsosScraper()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.scraper.close()
    
    @patch('selenium.webdriver.Firefox')
    def test_setup_driver(self, mock_firefox):
        """Test driver setup."""
        self.scraper.setup_driver()
        mock_firefox.assert_called_once()
    
    @patch('selenium.webdriver.Firefox')
    def test_wait_for_page_load(self, mock_firefox):
        """Test page load waiting."""
        # Mock the driver's execute_script method
        mock_driver = Mock()
        mock_driver.execute_script.side_effect = ['complete', 0]
        self.scraper.driver = mock_driver
        
        result = self.scraper.wait_for_page_load()
        self.assertTrue(result)
    
    @patch('selenium.webdriver.Firefox')
    def test_scrape_product(self, mock_firefox):
        """Test product scraping."""
        # Mock the driver and its methods
        mock_driver = Mock()
        mock_driver.page_source = """
        <html>
            <h1>Test Product</h1>
            <span data-testid="current-price">£85.00</span>
            <a href="/brand/test-brand">Test Brand</a>
            <div class="product-description">Test Description</div>
        </html>
        """
        self.scraper.driver = mock_driver
        
        result = self.scraper.scrape_product("https://www.asos.com/test-product")
        self.assertEqual(result['name'], "Test Product")
        self.assertEqual(result['price'], 85.00)
        self.assertEqual(result['brand'], "Test Brand")
        self.assertEqual(result['description'], "Test Description")
        self.assertEqual(result['url'], "https://www.asos.com/test-product")

if __name__ == '__main__':
    unittest.main() 