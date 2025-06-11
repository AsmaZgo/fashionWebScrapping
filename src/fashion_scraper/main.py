"""
Main script to run the fashion scraper.
"""
import argparse
import logging
from .asos.scraper import AsosScraper
from .utils.logger import setup_logger

def main():
    """Main function to run the scraper."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Fashion Web Scraper")
    parser.add_argument(
        "--site",
        choices=["asos"],
        default="asos",
        help="Website to scrape (default: asos)"
    )
    parser.add_argument(
        "--category",
        required=True,
        help="Category URL to scrape"
    )
    parser.add_argument(
        "--output",
        default="data/raw",
        help="Output directory for scraped data"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logger("fashion_scraper")
    logger.setLevel(log_level)
    
    try:
        # Initialize appropriate scraper
        if args.site == "asos":
            scraper = AsosScraper()
        else:
            raise ValueError(f"Unsupported site: {args.site}")
        
        # Get product links
        logger.info(f"Scraping category: {args.category}")
        product_links = scraper.get_product_links(args.category)
        logger.info(f"Found {len(product_links)} products")
        
        # Scrape each product
        for i, link in enumerate(product_links, 1):
            try:
                logger.info(f"Scraping product {i}/{len(product_links)}: {link}")
                product_data = scraper.scrape_product(link)
                logger.info(f"Successfully scraped product: {product_data.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error scraping product {link}: {str(e)}")
                continue
        
    except Exception as e:
        logger.error(f"Error running scraper: {str(e)}")
        raise
    finally:
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main() 