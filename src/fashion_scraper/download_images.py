import json
import logging
import os
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import time
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Common user agents to rotate through
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
]

def get_headers():
    """Get random headers for the request."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.asos.com/',
        'sec-ch-ua': '"Google Chrome";v="91", "Chromium";v="91"',
        'sec-ch-ua-mobile': '?0',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
    }

def transform_image_url(url: str) -> str:
    """Transform ASOS image URL to get the full resolution image."""
    # Remove size parameters and get base URL
    base_url = url.split('?')[0]
    
    # Remove any size indicators from the URL
    base_url = base_url.replace('-1-', '-1-')
    base_url = base_url.replace('-2-', '-2-')
    base_url = base_url.replace('-3-', '-3-')
    base_url = base_url.replace('-4-', '-4-')
    
    # Add full resolution parameters
    return f"{base_url}?$n_960w$&wid=951&fit=constrain"

def download_image(url: str, save_path: Path, max_retries: int = 3) -> bool:
    """Download a single image from URL with retries."""
    for attempt in range(max_retries):
        try:
            # Add random delay between 1-3 seconds
            time.sleep(random.uniform(1, 3))
            
            # Get the image with headers
            response = requests.get(
                url,
                headers=get_headers(),
                stream=True,
                timeout=15
            )
            response.raise_for_status()
            
            # Create directory if it doesn't exist
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the image
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.debug(f"Successfully downloaded: {url}")
            return True
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Exponential backoff
                logger.warning(f"Attempt {attempt + 1} failed for {url}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Error downloading {url} after {max_retries} attempts: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {str(e)}")
            return False

def get_image_filename(url: str, index: int) -> str:
    """Generate a filename for the image."""
    # Get the last part of the URL
    parsed = urlparse(url)
    path = parsed.path
    
    # Try to get the original filename
    original_name = os.path.basename(path)
    if original_name:
        # Remove any query parameters
        original_name = original_name.split('?')[0]
        # Add index to ensure uniqueness
        name, ext = os.path.splitext(original_name)
        return f"{name}_{index}{ext}"
    
    # Fallback to a generic name
    return f"image_{index}.jpg"

def process_product_json(json_path: Path, output_dir: Path) -> None:
    """Process a single product JSON file and download its images."""
    try:
        # Read the JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            product_data = json.load(f)
        
        # Get product ID and name
        product_id = product_data.get('product_id', 'unknown')
        product_name = product_data.get('product_info', {}).get('name', 'unknown')
        
        # Create product directory
        product_dir = output_dir / f"product_{product_id}"
        product_dir.mkdir(parents=True, exist_ok=True)
        
        # Get image URLs
        image_urls = product_data.get('product_info', {}).get('images', [])
        
        if not image_urls:
            logger.warning(f"No images found for product {product_id}")
            return
        
        logger.info(f"Processing product {product_id}: {product_name}")
        logger.info(f"Found {len(image_urls)} images")
        
        # Download images
        successful_downloads = 0
        for i, url in enumerate(image_urls, 1):
            filename = get_image_filename(url, i)
            save_path = product_dir / filename
            
            if download_image(url, save_path):
                successful_downloads += 1
                logger.info(f"Downloaded image {i}/{len(image_urls)} for product {product_id}")
            else:
                logger.error(f"Failed to download image {i}/{len(image_urls)} for product {product_id}")
        
        logger.info(f"Product {product_id}: Successfully downloaded {successful_downloads}/{len(image_urls)} images")
        
    except Exception as e:
        logger.error(f"Error processing {json_path}: {str(e)}")

def main():
    """Main function to download product images."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download product images from JSON files")
    parser.add_argument('--input', required=True, help="Directory containing product JSON files")
    parser.add_argument('--output', required=True, help="Directory to save downloaded images")
    parser.add_argument('--workers', type=int, default=2, help="Number of worker threads")
    parser.add_argument('--retries', type=int, default=3, help="Number of retry attempts per image")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all product JSON files
    json_files = list(input_dir.glob('**/product_*.json'))
    
    if not json_files:
        logger.error(f"No product JSON files found in {input_dir}")
        return
    
    logger.info(f"Found {len(json_files)} product JSON files")
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for json_file in json_files:
            executor.submit(process_product_json, json_file, output_dir)
    
    logger.info("Finished downloading images")

if __name__ == "__main__":
    main() 