import schedule
import time
import subprocess
import logging
from datetime import datetime
import os

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
    "https://www.asos.com/women/new-in/new-in-today/cat/?cid=51163",
    "https://www.asos.com/women/new-in/new-in-clothing/cat/?cid=2623",
    "https://www.asos.com/women/new-in/new-in-shoes/cat/?cid=6992",
    "https://www.asos.com/women/ctas/hub-edit-12/cat/?cid=51126",
    "https://www.asos.com/women/new-in/new-in-clothing/cat/?cid=2623&refine=attribute_10992:61379",
    "https://www.asos.com/women/a-to-z-of-brands/good-american/cat/?cid=52364"
]

def run_scraper(url):
    """Run the scraper for a specific URL"""
    try:
        # Create timestamp for unique output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"data/raw/{timestamp}"
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Construct the command
        cmd = [
            "python", "-m", "src.fashion_scraper.main",
            "--category", url,
            "--output", output_dir,
            "--debug"
        ]
        
        logging.info(f"Starting scraper for URL: {url}")
        logging.info(f"Output directory: {output_dir}")
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Log the output
        if result.stdout:
            logging.info(f"Command output: {result.stdout}")
        if result.stderr:
            logging.error(f"Command error: {result.stderr}")
            
        logging.info(f"Completed scraping for URL: {url}")
        
    except Exception as e:
        logging.error(f"Error running scraper for URL {url}: {str(e)}")

def schedule_jobs():
    """Schedule all scraping jobs"""
    # Schedule each URL to run every 30 minutes
    for url in URLS:
        schedule.every(30).minutes.do(run_scraper, url)
    
    logging.info("All jobs scheduled. Running every 30 minutes.")
    
    # Run the jobs immediately on startup
    for url in URLS:
        run_scraper(url)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    logging.info("Starting scheduler")
    schedule_jobs() 