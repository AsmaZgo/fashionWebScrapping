"""
Data storage utilities for fashion scrapers.
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Union
from datetime import datetime

class DataStorage:
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "raw"
        self.processed_dir = self.base_dir / "processed"
        
        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def save_json(self, data: Union[Dict, List], filename: str, subdir: str = None):
        """Save data to JSON file."""
        if subdir:
            save_dir = self.raw_dir / subdir
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            save_dir = self.raw_dir

        filepath = save_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_csv(self, data: List[Dict], filename: str, subdir: str = None):
        """Save data to CSV file."""
        if subdir:
            save_dir = self.raw_dir / subdir
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            save_dir = self.raw_dir

        filepath = save_dir / f"{filename}.csv"
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8')

    def load_json(self, filename: str, subdir: str = None) -> Union[Dict, List]:
        """Load data from JSON file."""
        if subdir:
            filepath = self.raw_dir / subdir / f"{filename}.json"
        else:
            filepath = self.raw_dir / f"{filename}.json"

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_csv(self, filename: str, subdir: str = None) -> pd.DataFrame:
        """Load data from CSV file."""
        if subdir:
            filepath = self.raw_dir / subdir / f"{filename}.csv"
        else:
            filepath = self.raw_dir / f"{filename}.csv"

        return pd.read_csv(filepath)

    def process_data(self, data: List[Dict]) -> pd.DataFrame:
        """Process raw data into a clean DataFrame."""
        # Flatten nested structure
        processed_data = []
        for item in data:
            product_info = item['product_info']
            source = item['source']
            
            flat_item = {
                'product_id': item['product_id'],
                'website': source['website'],
                'url': source['url'],
                'scraped_at': source['scraped_at'],
                'name': product_info['name'],
                'price': product_info['price'],
                'currency': product_info['currency'],
                'description': product_info['description'],
                'sizes': ','.join(product_info['sizes']),
                'colors': ','.join(product_info['colors']),
                'images': ','.join(product_info['images']),
                'review_count': len(item.get('reviews', []))
            }
            processed_data.append(flat_item)
        
        return pd.DataFrame(processed_data)

    def save_processed_data(self, df: pd.DataFrame, filename: str):
        """Save processed data to CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.processed_dir / f"{filename}_{timestamp}.csv"
        df.to_csv(filepath, index=False, encoding='utf-8') 