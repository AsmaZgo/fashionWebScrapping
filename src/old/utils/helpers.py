import re
from typing import Optional
from datetime import datetime
import logging
from pathlib import Path
import sys

# Set up logging
def setup_logging(log_dir: str = "logs", debug: bool = False):
    """Set up logging configuration.
    
    Args:
        log_dir (str): Directory to store log files
        debug (bool): If True, sets logging level to DEBUG and adds more detailed formatting
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"scraper_{timestamp}.log"
    
    # Set logging level based on debug mode
    level = logging.DEBUG if debug else logging.INFO
    
    # Create formatters
    if debug:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
    
    # Create handlers
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels for external libraries
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized with level: {logging.getLevelName(level)}")
    logger.info(f"Log file: {log_file}")
    
    return logger

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and special characters."""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text)
    return text.strip()

def extract_price(price_text: str) -> Optional[float]:
    """Extract price from text."""
    if not price_text:
        return None
    
    # Remove currency symbols and other non-numeric characters
    price = re.sub(r'[^\d.,]', '', price_text)
    
    # Handle different decimal separators
    if ',' in price and '.' in price:
        # If both separators exist, assume the last one is the decimal separator
        parts = price.split('.')
        price = parts[0].replace(',', '') + '.' + parts[-1]
    else:
        price = price.replace(',', '.')
    
    try:
        return float(price)
    except ValueError:
        return None

def extract_product_id(url: str) -> Optional[str]:
    """Extract product ID from URL."""
    # Common patterns for product IDs in URLs
    patterns = [
        r'/prd/(\d+)',  # ASOS pattern
        r'/product/(\d+)',  # Generic pattern
        r'/item/(\d+)',  # Another common pattern
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp in ISO format."""
    return timestamp.isoformat()

def create_filename(prefix: str, extension: str = 'json') -> str:
    """Create a filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}" 