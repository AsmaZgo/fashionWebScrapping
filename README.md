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

1. Configure the target websites in the configuration file
2. Run the main script:
```bash
python src/main.py
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
