"""
Main script to run the fashion scraper.
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import json

from .asos import AsosScraper
from .utils.logger import setup_logger
from .utils.data_storage import DataStorage

def validate_asos_url(url: str) -> bool:
    """Validate ASOS category URL."""
    return url.startswith("https://www.asos.com/") and "/cat/" in url

def extract_category_name(url: str) -> str:
    """Extract category name from ASOS URL."""
    try:
        # Remove query parameters and trailing slash
        clean_url = url.split("?")[0].rstrip("/")
        # Get the last part of the URL
        category = clean_url.split("/")[-2]
        return category
    except:
        return "unknown_category"

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
        help="Category URL to scrape (e.g., https://www.asos.com/men/new-in/new-in-clothing/cat/?cid=6993)"
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
    
    # Log the start of the script
    logger.info("Starting fashion scraper")
    logger.debug(f"Arguments: {args}")
    
    # Validate category URL
    if args.site == "asos" and not validate_asos_url(args.category):
        logger.error(f"Invalid ASOS category URL: {args.category}")
        logger.error("Please use a valid ASOS URL (e.g., https://www.asos.com/men/new-in/new-in-clothing/cat/?cid=6993)")
        return
    
    # Initialize data storage
    storage = DataStorage(base_dir=args.output)
    logger.debug(f"Initialized data storage in {args.output}")
    
    try:
        # Initialize appropriate scraper
        if args.site == "asos":
            logger.info("Initializing ASOS scraper")
            scraper = AsosScraper()
        else:
            raise ValueError(f"Unsupported site: {args.site}")
        
        # Extract category name from URL for file naming
        category_name = extract_category_name(args.category)
        logger.info(f"Category name extracted: {category_name}")
        
        # Get product links
        logger.info(f"Scraping category: {args.category}")
        try:
            product_links = scraper.get_product_links(args.category)
            logger.info(f"Found {len(product_links)} products")
            logger.debug(f"First few product links: {product_links[:3]}")
        except Exception as e:
            logger.error(f"Error getting product links: {str(e)}", exc_info=True)
            raise
        
        # Scrape each product
        scraped_products = []
        for i, link in enumerate(product_links, 1):
            try:
                logger.info(f"Scraping product {i}/{len(product_links)}: {link}")
                product_data = scraper.scrape_product(link)
                
                if not product_data:
                    logger.warning(f"No data returned for product: {link}")
                    continue
                
                # Format product data for storage
                formatted_data = {
                    'product_id': product_data.get('id', str(i)),
                    'source': {
                        'website': args.site,
                        'url': link,
                        'scraped_at': datetime.now().isoformat(),
                        'category': category_name
                    },
                    'product_info': {
                        'name': product_data.get('name', ''),
                        'price': product_data.get('price', 0.0),
                        'currency': 'GBP',  # ASOS uses GBP
                        'description': product_data.get('description', ''),
                        'sizes': product_data.get('sizes', []),
                        'colors': product_data.get('colors', []),
                        'images': product_data.get('images', []),
                        'materials': product_data.get('materials', []),
                        'details': product_data.get('details', []),
                        'product_code': product_data.get('product_code', ''),
                        'brand': product_data.get('brand', ''),
                        'brand_details': product_data.get('brand_details', ''),
                        'about_me': product_data.get('about_me', ''),
                        'saved_count': product_data.get('saved_count'),
                        'ratings': product_data.get('ratings', {}),
                        'recent_review': product_data.get('recent_review', {})
                    },
                    'reviews': product_data.get('reviews', [])
                }
                
                scraped_products.append(formatted_data)
                logger.info(f"Successfully scraped product: {product_data.get('name', 'Unknown')}")
                
                # Save individual product data
                try:
                    # Save main product data
                    storage.save_json(
                        formatted_data,
                        f"product_{formatted_data['product_id']}",
                        subdir=f"{args.site}/{category_name}"
                    )
                    logger.debug(f"Saved individual product data for: {formatted_data['product_id']}")

                    # Save individual review files
                    if 'all_reviews' in product_data and product_data['all_reviews']:
                        reviews_dir = Path(args.output) / args.site / category_name / 'reviews'
                        reviews_dir.mkdir(parents=True, exist_ok=True)
                        
                        for i, review in enumerate(product_data['all_reviews'], 1):
                            review_data = {
                                'product_id': formatted_data['product_id'],
                                'product_name': formatted_data['product_info']['name'],
                                'review_number': i,
                                'review': review
                            }
                            
                            review_filename = f"review_{formatted_data['product_id']}_{i}.json"
                            review_path = reviews_dir / review_filename
                            
                            with open(review_path, 'w', encoding='utf-8') as f:
                                json.dump(review_data, f, indent=2, ensure_ascii=False)
                            
                            logger.debug(f"Saved review {i} for product {formatted_data['product_id']}")
                except Exception as e:
                    logger.error(f"Error saving individual product data: {str(e)}", exc_info=True)
                
            except Exception as e:
                logger.error(f"Error scraping product {link}: {str(e)}", exc_info=True)
                continue
        
        # Save all products in a single file
        if scraped_products:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                storage.save_json(
                    scraped_products,
                    f"products_{category_name}_{timestamp}",
                    subdir=f"{args.site}/{category_name}"
                )
                logger.info(f"Saved combined product data for {len(scraped_products)} products")
                
                # Process and save as CSV
                df = storage.process_data(scraped_products)
                storage.save_processed_data(df, f"products_{args.site}_{category_name}")
                logger.info(f"Saved processed CSV data")
                
                logger.info(f"Successfully saved {len(scraped_products)} products to {args.output}/{args.site}/{category_name}")
            except Exception as e:
                logger.error(f"Error saving combined product data: {str(e)}", exc_info=True)
        else:
            logger.warning("No products were successfully scraped")
        
    except Exception as e:
        logger.error(f"Error running scraper: {str(e)}", exc_info=True)
        raise
    finally:
        if 'scraper' in locals():
            logger.info("Closing scraper")
            scraper.close()

if __name__ == "__main__":
    main() 