# Fashion Web Scraping Project

This project is designed to scrape fashion websites for clothing items, their features, and user comments. The scraped data is stored in both JSON and CSV formats for future data processing and analysis.

## Project Structure

```
fashionWebScrapping/
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── asos_scraper.py
│   │   └── zara_scraper.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_storage.py
│   │   └── helpers.py
│   └── main.py
├── data/
│   ├── raw/
│   └── processed/
├── requirements.txt
└── README.md
```

## Features

- Scrapes multiple fashion websites (ASOS, Zara, etc.)
- Extracts detailed product information:
  - Product name
  - Price
  - Description
  - Sizes available
  - Colors
  - Materials
  - User reviews and ratings
  - Product images URLs
- Stores data in both JSON and CSV formats
- Includes source URL and timestamp for each scraped item
- Implements rate limiting and respect robots.txt
- Handles pagination for product listings

## Requirements

- Python 3.8+
- Required packages (see requirements.txt):
  - requests
  - beautifulsoup4
  - selenium
  - pandas
  - fake-useragent
  - python-dotenv

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fashionWebScrapping.git
cd fashionWebScrapping
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Refactored Main Script

The main script can be run in two ways:

1. Using the command-line interface:
```bash
python -m fashion_scraper.main --site asos --category "https://www.asos.com/men/" --output data/raw --debug
```

Arguments:
- `--site`: Website to scrape (currently only "asos" is supported)
- `--category`: Category URL to scrape (required)
- `--output`: Output directory for scraped data (default: "data/raw")
- `--debug`: Enable debug logging (optional)

2. Using the Python API:
```python
from fashion_scraper.asos import AsosScraper

# Initialize the scraper
scraper = AsosScraper()

try:
    # Get product links from a category
    category_url = "https://www.asos.com/men/"
    product_links = scraper.get_product_links(category_url)
    
    # Scrape each product
    for link in product_links:
        product_data = scraper.scrape_product(link)
        print(f"Scraped product: {product_data['name']}")
        
finally:
    # Always close the scraper when done
    scraper.close()
```

## Development

### Running Tests

Run the test suite:
```bash
pytest src/fashion_scraper/tests/
```

Run tests with coverage:
```bash
pytest --cov=src/fashion_scraper src/fashion_scraper/tests/
```

### Code Style

The project uses:
- `black` for code formatting
- `isort` for import sorting
- `flake8` for linting

Format code:
```bash
black src/
isort src/
```

Check code style:
```bash
flake8 src/
```

## Data Structure

### JSON Format
```json
{
    "product_id": "string",
    "source": {
        "website": "string",
        "url": "string",
        "scraped_at": "timestamp"
    },
    "product_info": {
        "name": "string",
        "price": "float",
        "currency": "string",
        "description": "string",
        "sizes": ["string"],
        "colors": ["string"],
        "materials": ["string"],
        "images": ["url_string"]
    },
    "reviews": [
        {
            "user_id": "string",
            "rating": "integer",
            "comment": "string",
            "date": "timestamp"
        }
    ]
}
```

### CSV Format
The CSV files will contain the same information in a flattened structure, with separate files for products and reviews.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This project is for educational purposes only. Please respect the terms of service and robots.txt of the websites you scrape. Implement appropriate delays between requests to avoid overloading the servers.
