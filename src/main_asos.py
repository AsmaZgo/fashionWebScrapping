import logging
import json
from pathlib import Path
from scrapers.asos_scraper import AsosScraper

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('asos_debug.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    logger.debug("Starting ASOS scraper in debug mode")
    asos_scraper = AsosScraper()
    try:
        logger.info("Starting ASOS scraping...")
        asos_products = asos_scraper.scrape_category(
            "https://www.asos.com/men/",
            max_products=100
        )
        asos_output_file = data_dir / "asos_products.json"
        with open(asos_output_file, 'w', encoding='utf-8') as f:
            json.dump(asos_products, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(asos_products)} ASOS products to {asos_output_file}")
    except Exception as e:
        logger.error(f"Error during ASOS scraping: {str(e)}", exc_info=True)
    finally:
        logger.debug("Closing ASOS scraper")
        asos_scraper.close()

if __name__ == "__main__":
    main() 