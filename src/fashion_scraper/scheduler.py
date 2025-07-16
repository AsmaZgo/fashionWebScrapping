import subprocess
import logging
from datetime import datetime
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

# List of URLs to scrape
URLS = [
    "https://www.asos.com/men/new-in/cat/?cid=27110&refine=attribute_1047:8414,8415",
    "https://www.asos.com/men/new-in/new-in-clothing/cat/?cid=6993&currentpricerange=5-440&refine=attribute_1047:8386",
    "https://www.asos.com/men/new-in/new-in-clothing/cat/?cid=6993&refine=attribute_1047:8391,8405#nlid=mw|new+in|new+products|hoodies+%26+sweatshirts",
    "https://www.asos.com/men/new-in/new-in-clothing/cat/?cid=6993&refine=attribute_10992:61394#nlid=mw|new+in|new+products|swimwear",
    "https://www.asos.com/men/new-in/cat/?cid=27110&refine=attribute_10992:61377",
    "https://www.asos.com/men/new-in/new-in-accessories/cat/?cid=27112",
    "https://www.asos.com/women/new-in/new-in-today/cat/?cid=51163",
    "https://www.asos.com/women/new-in/new-in-clothing/cat/?cid=2623",
    "https://www.asos.com/women/new-in/new-in-shoes/cat/?cid=6992",
    "https://www.asos.com/women/ctas/hub-edit-12/cat/?cid=51126",
    "https://www.asos.com/women/new-in/new-in-clothing/cat/?cid=2623&refine=attribute_10992:61379",
    "https://www.asos.com/women/a-to-z-of-brands/good-american/cat/?cid=52364",
    "https://www.asos.com/women/swimwear-beachwear/cat/?cid=2238&refine=freshness_band:4",
    "https://www.asos.com/women/new-in/new-in-clothing/cat/?cid=2623&currentpricerange=5-430&refine=attribute_1047:8386",
    "https://www.asos.com/women/new-in/new-in-face-body/cat/?cid=2426",
    "https://www.asos.com/women/new-in/new-in-accessories/cat/?cid=27109",
    "https://www.asos.com/women/seasonal/summer-essentials/cat/?cid=50090",
    "https://www.asos.com/women/trends/linen-clothing/cat/?cid=51702",
    "https://www.asos.com/women/festival/cat/?cid=7662",
    "https://www.asos.com/women/seasonal/summer-essentials/summer-dresses/cat/?cid=10860",
    "https://www.asos.com/women/trends/crochet/cat/?cid=50528",
    "https://www.asos.com/women/outfits/airport-outfits/cat/?cid=51343", "https://www.asos.com/women/your-most-hyped/co-ords/cat/?cid=52775"
,"https://www.asos.com/women/ctas/hub-edit-14/cat/?cid=51129"
  , "https://www.asos.com/women/ctas/womens-email-1/cat/?cid=17538"  ,
    "https://www.asos.com/men/new-in/new-in-clothing/cat/?cid=6993",
    "https://www.asos.com/men/new-in/new-in-shoes/cat/?cid=17184",
    "https://www.asos.com/men/new-in/new-in-today/cat/?cid=51164",
    "https://www.asos.com/men/ctas/hub-edit-2/cat/?cid=51137"
 ]


PAUSE_SECONDS = 3 * 60  # 3 minutes

def run_scraper(url):
    """Run the scraper for a specific URL"""
    try:
        # Create timestamp for unique output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"data/raw/{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        cmd = [
            "python", "-m", "src.fashion_scraper.main",
            "--category", url,
            "--output", output_dir,
            "--debug"
        ]
        logging.info(f"Starting scraper for URL: {url}")
        logging.info(f"Output directory: {output_dir}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            logging.info(f"Command output: {result.stdout}")
        if result.stderr:
            logging.error(f"Command error: {result.stderr}")
        logging.info(f"Completed scraping for URL: {url}")
    except Exception as e:
        logging.error(f"Error running scraper for URL {url}: {str(e)}")

def main():
    logging.info("Sequential scheduler started. Will pause 5 minutes between each URL.")
    for idx, url in enumerate(URLS):
        run_scraper(url)
        if idx < len(URLS) - 1:
            logging.info(f"Waiting 5 minutes before next URL...")
            time.sleep(PAUSE_SECONDS)
    logging.info("All URLs processed. Scheduler exiting.")

if __name__ == "__main__":
    main() 