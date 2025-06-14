from fashion_scraper.asos import AsosScraper

def main():
    # Use a specific category URL for testing
    category_url = "https://www.asos.com/men/new-in/new-in-clothing/cat/?cid=6993"
    scraper = AsosScraper()
    try:
        print("Getting product links...")
        product_links = scraper.get_product_links(category_url)
        if not product_links:
            print("No product links found.")
            return
        first_link = product_links[0]
        print(f"First product link: {first_link}")

        print("Scraping first product...")
        product_data = scraper.scrape_product(first_link)
        print("\nExtracted product data:")
        for k, v in product_data.items():
            print(f"{k}: {v}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 