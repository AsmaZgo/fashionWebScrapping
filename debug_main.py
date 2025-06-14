import logging
import pdb
from fashion_scraper.asos import AsosScraper

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Initialize scraper
    scraper = AsosScraper()
    
    try:
        # Test URL
        category_url = "https://www.asos.com/men/new-in/new-in-clothing/cat/?cid=6993"
        
        # Get product links
        print("\nGetting product links...")
        product_links = scraper.get_product_links(category_url)
        
        if not product_links:
            print("No product links found!")
            return
            
        # Get first product
        first_link = product_links[0]
        print(f"\nFirst product link: {first_link}")
        
        # Set breakpoint here to inspect product_links
        pdb.set_trace()
        
        # Scrape first product
        print("\nScraping first product...")
        product_data = scraper.scrape_product(first_link)
        
        # Print results
        print("\nExtracted product data:")
        for key, value in product_data.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        # Set breakpoint on error
        pdb.set_trace()
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 