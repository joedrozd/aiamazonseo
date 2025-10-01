# AI Amazon SEO - Web Scraping Tools

A collection of Python tools for web scraping and data collection, featuring an Amazon product scraper for SEO and market research.

## Features

### Amazon Product Scraper (`amazon_scraper.py`)

- **Keyword-based search**: Search Amazon products using multiple keywords
- **Comprehensive data extraction**: Extracts title, price, rating, reviews, images, and ASIN
- **Pagination support**: Automatically handles multiple search result pages
- **Rate limiting**: Built-in delays and user-agent rotation for responsible scraping
- **Dual scraping modes**: Choose between requests/BeautifulSoup or Selenium for JavaScript-heavy pages
- **Error handling**: Robust error handling and logging
- **JSON export**: Save scraped data to JSON files for further analysis

## Getting Started

### Prerequisites
- Python 3.7 or higher
- Chrome browser (for Selenium mode)
- LM Studio
### LM Studio use 

This project uses LM Studio to run LLMs directly on localhost, enabling fast, private, and offline inference without relying on external APIs. By hosting models locally, I can control system resources, test integrations in a contained environment, and ensure reproducibility across setups.

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Amazon Product Scraper

#### Command Line Usage

```bash
# Basic usage - search for products and export links list
python amazon_scraper.py --keywords "wireless headphones"

# Search multiple keywords and export all formats (JSON, TXT, CSV)
python amazon_scraper.py --keywords "wireless headphones" "bluetooth speakers"

# Export only product links in text format
python amazon_scraper.py \
  --keywords "laptop" "gaming mouse" \
  --format txt \
  --output product_links

# Export product links in CSV format for spreadsheet analysis
python amazon_scraper.py \
  --keywords "smartphone" \
  --format csv \
  --output mobile_products

# Advanced usage with custom limits and JSON export
python amazon_scraper.py \
  --keywords "laptop" "gaming mouse" \
  --max-pages 5 \
  --max-products 100 \
  --format json \
  --output my_products

# Use Selenium for JavaScript-heavy scraping
python amazon_scraper.py \
  --keywords "smartphone" \
  --selenium \
  --headless
```

#### Python API Usage

```python
from amazon_scraper import AmazonScraper

# Initialize scraper
scraper = AmazonScraper()

# Search for products
keywords = ["wireless headphones", "bluetooth speakers"]
products = scraper.search_products(keywords, max_pages=3, max_products=50)

# Save comprehensive data to JSON
scraper.save_to_json(products, "amazon_products.json")

# Save product links list in text format
scraper.save_product_links(products, "product_links", format='txt')

# Save product links in CSV format for spreadsheet analysis
scraper.save_product_links(products, "product_links", format='csv')

# Clean up
scraper.close()

# Example product data structure:
# {
#   "title": "Sony WH-1000XM4 Wireless Industry Leading Noise Canceling Overhead Headphones",
#   "price": "278.00",
#   "rating": 4.6,
#   "reviews_count": 28453,
#   "url": "https://www.amazon.com/dp/B0863TXGM3",
#   "image_url": "https://m.media-amazon.com/images/I/71o8Q5XJS5L._AC_UL320_.jpg",
#   "asin": "B0863TXGM3",
#   "search_keyword": "wireless headphones"
# }
```

#### Export Formats

**Text Format (.txt)** - Human-readable list:
```
AMAZON PRODUCT LINKS

1. Sony WH-1000XM4 Wireless Industry Leading Noise Canceling Overhead Headphones
   Link: https://www.amazon.com/dp/B0863TXGM3
   Price: 278.00
   Rating: 4.6
   Keyword: wireless headphones
--------------------------------------------------

2. Bose QuietComfort 35 II Wireless Bluetooth Headphones
   Link: https://www.amazon.com/dp/B0756CYWWD
   Price: 249.00
   Rating: 4.4
   Keyword: wireless headphones
--------------------------------------------------
```

**CSV Format (.csv)** - Spreadsheet-compatible:
```csv
Title,URL,Price,Rating,Search Keyword
Sony WH-1000XM4 Wireless Industry Leading Noise Canceling Overhead Headphones,https://www.amazon.com/dp/B0863TXGM3,278.00,4.6,wireless headphones
Bose QuietComfort 35 II Wireless Bluetooth Headphones,https://www.amazon.com/dp/B0756CYWWD,249.00,4.4,wireless headphones
```

#### Using Selenium Mode

For pages with heavy JavaScript or anti-bot measures:

```python
# Initialize with Selenium
scraper = AmazonScraper(use_selenium=True, headless=True)

# The rest of the API is the same
products = scraper.search_products(["smartphone"])
```

### Chat API Client (`main.py`)

A simple client for interacting with chat completion APIs:

```bash
python main.py
```

## Project Structure

- `amazon_scraper.py` - Amazon product scraper with comprehensive features
- `main.py` - Chat API client for testing API endpoints
- `requirements.txt` - Project dependencies
- `README.md` - Project documentation

## Scraping Best Practices

- **Respect robots.txt**: Always check Amazon's robots.txt before scraping
- **Rate limiting**: The scraper includes built-in delays to avoid overwhelming servers
- **User agent rotation**: Uses various user agents to distribute requests
- **Legal compliance**: Ensure your use case complies with Amazon's Terms of Service
- **Data usage**: Use scraped data responsibly and in accordance with applicable laws

## Configuration

### Rate Limiting

The scraper includes configurable rate limiting:
- Default delay: 1-3 seconds between requests
- Configurable via `min_delay` and `max_delay` attributes

### User Agents

Pre-configured user agents for different browsers and platforms. Easily extensible by modifying the `user_agents` list.

## Error Handling

The scraper includes comprehensive error handling for:
- Network timeouts and connection errors
- HTML parsing failures
- Rate limiting and anti-bot measures
- Invalid or missing product data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is for educational and research purposes only. Always respect website terms of service and robots.txt files. The authors are not responsible for misuse of this software.
