#!/usr/bin/env python3
"""
Amazon Product Scraper

A web scraper that targets Amazon products related to specified keywords.
Extracts product information including title, price, rating, reviews, and more.
"""

import requests
import time
import random
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AmazonScraper:
    """
    Amazon product scraper with keyword-based search functionality.
    """

    def __init__(self, use_selenium: bool = False, headless: bool = True, affiliate_id: str = "cyberheroes-20"):
        """
        Initialize the Amazon scraper.

        Args:
            use_selenium: Whether to use Selenium for JavaScript-heavy pages
            headless: Whether to run browser in headless mode (Selenium only)
            affiliate_id: Amazon affiliate tracking ID
        """
        self.use_selenium = use_selenium
        self.headless = headless
        self.affiliate_id = affiliate_id
        self.session = requests.Session()
        self.driver = None

        # Amazon base URLs
        self.base_url = "https://www.amazon.com"
        self.search_url = "https://www.amazon.com/s"

        # User agents for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

        # Rate limiting
        self.min_delay = 1.0  # Minimum delay between requests
        self.max_delay = 3.0  # Maximum delay between requests
        self.last_request_time = 0

        # Initialize Selenium if requested
        if self.use_selenium:
            self._init_selenium()

    def _init_selenium(self):
        """Initialize Selenium WebDriver."""
        try:
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False

    def _get_random_user_agent(self) -> str:
        """Get a random user agent for request headers."""
        return random.choice(self.user_agents)

    def _rate_limit(self):
        """Implement rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            sleep_time = random.uniform(self.min_delay, self.max_delay)
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _add_affiliate_tag(self, url: str) -> str:
        """
        Add affiliate tracking tag to Amazon product URL.

        Args:
            url: The original product URL

        Returns:
            URL with affiliate tag appended
        """
        if not url or not self.affiliate_id:
            return url

        from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Add the affiliate tag
        query_params['tag'] = [self.affiliate_id]

        # Reconstruct the URL with the new query parameters
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))

        return new_url

    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Make an HTTP request with proper headers and rate limiting.

        Args:
            url: The URL to request
            params: Optional query parameters

        Returns:
            HTML content as string, or None if failed
        """
        self._rate_limit()

        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        try:
            if params:
                full_url = f"{url}?{urlencode(params)}"
            else:
                full_url = url

            logger.info(f"Making request to: {full_url}")
            response = self.session.get(full_url, headers=headers, timeout=30)
            response.raise_for_status()

            return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def _selenium_get_page(self, url: str) -> Optional[str]:
        """Get page content using Selenium."""
        if not self.driver:
            return None

        try:
            self.driver.get(url)
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
            )
            # Additional wait for dynamic content
            time.sleep(2)
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Selenium request failed: {e}")
            return None

    def _extract_product_data(self, product_element) -> Optional[Dict[str, Any]]:
        """
        Extract product data from a BeautifulSoup element.

        Args:
            product_element: BeautifulSoup element containing product data

        Returns:
            Dictionary with product information
        """
        try:
            product_data = {}

            # Product title - try multiple selectors
            title_elem = None
            title_selectors = [
                'h2.a-size-mini a.a-link-normal',
                'h2.a-size-medium a.a-link-normal',
                'span.a-size-medium a.a-link-normal',
                'span.a-size-base-plus a.a-link-normal',
                'a.a-link-normal h2',
                'a.a-link-normal span.a-text-normal'
            ]

            for selector in title_selectors:
                title_elem = product_element.select_one(selector)
                if title_elem:
                    break

            if not title_elem:
                # Fallback to broader search
                title_elem = product_element.find('a', class_='a-link-normal')

            product_data['title'] = title_elem.get_text().strip() if title_elem else None

            # Product URL
            if title_elem and title_elem.name == 'a':
                link_elem = title_elem
            else:
                link_elem = product_element.find('a', class_='a-link-normal')

            if link_elem and 'href' in link_elem.attrs:
                raw_url = urljoin(self.base_url, link_elem['href'])
                product_data['url'] = self._add_affiliate_tag(raw_url)
            else:
                product_data['url'] = None

            # Price - try multiple selectors
            price = None
            price_selectors = [
                'span.a-price .a-offscreen',
                'span.a-price-whole',
                'span.a-color-base',
                '.a-price .a-offscreen'
            ]

            for selector in price_selectors:
                price_elem = product_element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    # Clean up price text
                    price_text = re.sub(r'[^\d.]', '', price_text)
                    if price_text:
                        price = price_text
                        break

            product_data['price'] = price

            # Rating
            rating_elem = product_element.find('span', class_='a-icon-alt') or \
                         product_element.select_one('i.a-icon-star-small span.a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                # Extract numeric rating from "4.5 out of 5 stars"
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                product_data['rating'] = float(rating_match.group(1)) if rating_match else None
            else:
                product_data['rating'] = None

            # Number of reviews
            reviews_elem = product_element.find('span', class_='a-size-base') or \
                          product_element.select_one('span.a-size-small span.a-link-normal')
            if reviews_elem:
                reviews_text = reviews_elem.get_text().strip()
                reviews_match = re.search(r'\(?(\d+(?:,\d+)*)\)?', reviews_text)
                if reviews_match:
                    product_data['reviews_count'] = int(reviews_match.group(1).replace(',', ''))
                else:
                    product_data['reviews_count'] = None
            else:
                product_data['reviews_count'] = None

            # Product image
            img_elem = product_element.find('img', class_='s-image') or \
                      product_element.find('img')
            product_data['image_url'] = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None

            # ASIN (Amazon Standard Identification Number)
            if product_data['url']:
                asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_data['url'])
                product_data['asin'] = asin_match.group(1) if asin_match else None
            else:
                product_data['asin'] = None

            return product_data

        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None

    def search_products(self, keywords: List[str], max_pages: int = 3, max_products: int = 50) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon based on keywords.

        Args:
            keywords: List of keywords to search for
            max_pages: Maximum number of pages to scrape
            max_products: Maximum number of products to return

        Returns:
            List of product dictionaries
        """
        all_products = []

        for keyword in keywords:
            logger.info(f"Searching for products related to: {keyword}")

            for page in range(1, max_pages + 1):
                if len(all_products) >= max_products:
                    break

                # Prepare search parameters
                params = {
                    'k': keyword,
                    'page': page,
                    'ref': f'sr_pg_{page}'
                }

                # Make request
                if self.use_selenium:
                    html = self._selenium_get_page(f"{self.search_url}?{urlencode(params)}")
                else:
                    html = self._make_request(self.search_url, params)

                if not html:
                    logger.warning(f"Failed to get page {page} for keyword '{keyword}'")
                    continue

                # Parse HTML
                soup = BeautifulSoup(html, 'lxml')

                # Find product containers
                products = soup.find_all('div', {'data-component-type': 's-search-result'})

                if not products:
                    # Try alternative selectors
                    products = soup.find_all('div', class_='s-result-item')

                logger.info(f"Found {len(products)} products on page {page} for '{keyword}'")

                # Extract product data
                for product in products:
                    if len(all_products) >= max_products:
                        break

                    product_data = self._extract_product_data(product)
                    if product_data and product_data['title']:
                        product_data['search_keyword'] = keyword
                        all_products.append(product_data)

                # Check if there's a next page
                next_page = soup.find('a', {'aria-label': 'Go to next page'})
                if not next_page:
                    break

                # Add small delay between pages
                time.sleep(random.uniform(1.0, 2.0))

            if len(all_products) >= max_products:
                break

        logger.info(f"Total products scraped: {len(all_products)}")
        return all_products

    def save_to_json(self, products: List[Dict[str, Any]], filename: str):
        """
        Save scraped products to a JSON file.

        Args:
            products: List of product dictionaries
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            logger.info(f"Products saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save products to file: {e}")

    def save_product_links(self, products: List[Dict[str, Any]], filename: str, format: str = 'txt'):
        """
        Save products as a simple list with titles and links.

        Args:
            products: List of product dictionaries
            filename: Output filename (without extension)
            format: Output format - 'txt' or 'csv'
        """
        try:
            if format.lower() == 'csv':
                # CSV format
                csv_filename = f"{filename}.csv"
                with open(csv_filename, 'w', encoding='utf-8', newline='') as f:
                    import csv
                    writer = csv.writer(f)
                    writer.writerow(['Title', 'URL', 'Price', 'Rating', 'Search Keyword'])

                    for product in products:
                        writer.writerow([
                            product.get('title', ''),
                            product.get('url', ''),
                            product.get('price', ''),
                            product.get('rating', ''),
                            product.get('search_keyword', '')
                        ])
                logger.info(f"Product links saved to {csv_filename}")

            else:
                # Text format
                txt_filename = f"{filename}.txt"
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write("AMAZON PRODUCT LINKS\n")
                    f.write("=" * 50 + "\n\n")

                    for i, product in enumerate(products, 1):
                        title = product.get('title', 'N/A')
                        url = product.get('url', 'N/A')
                        price = product.get('price', 'N/A')
                        rating = product.get('rating', 'N/A')
                        keyword = product.get('search_keyword', 'N/A')

                        f.write(f"{i}. {title}\n")
                        f.write(f"   Link: {url}\n")
                        f.write(f"   Price: {price}\n")
                        f.write(f"   Rating: {rating}\n")
                        f.write(f"   Keyword: {keyword}\n")
                        f.write("-" * 50 + "\n\n")

                logger.info(f"Product links saved to {txt_filename}")

        except Exception as e:
            logger.error(f"Failed to save product links: {e}")

    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed")

def main():
    """Example usage of the Amazon scraper."""
    import argparse

    parser = argparse.ArgumentParser(description='Amazon Product Scraper')
    parser.add_argument('--keywords', nargs='+', required=True,
                       help='Keywords to search for (space-separated)')
    parser.add_argument('--max-pages', type=int, default=3,
                       help='Maximum pages to scrape per keyword')
    parser.add_argument('--max-products', type=int, default=50,
                       help='Maximum products to scrape')
    parser.add_argument('--output', default='amazon_products',
                       help='Output filename (without extension)')
    parser.add_argument('--format', choices=['json', 'txt', 'csv', 'all'],
                       default='all', help='Output format: json, txt, csv, or all')
    parser.add_argument('--selenium', action='store_true',
                       help='Use Selenium for scraping')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (Selenium only)')
    parser.add_argument('--affiliate-id', default='cyberheroes-20',
                       help='Amazon affiliate tracking ID (default: cyberheroes-20)')

    args = parser.parse_args()

    # Initialize scraper
    scraper = AmazonScraper(use_selenium=args.selenium, headless=args.headless, affiliate_id=args.affiliate_id)

    try:
        # Search for products
        products = scraper.search_products(
            keywords=args.keywords,
            max_pages=args.max_pages,
            max_products=args.max_products
        )

        # Save results based on format
        if args.format in ['json', 'all']:
            json_file = f"{args.output}.json"
            scraper.save_to_json(products, json_file)
            print(f"JSON results saved to {json_file}")

        if args.format in ['txt', 'all']:
            scraper.save_product_links(products, args.output, format='txt')
            print(f"Product links saved to {args.output}.txt")

        if args.format in ['csv', 'all']:
            scraper.save_product_links(products, args.output, format='csv')
            print(f"Product links saved to {args.output}.csv")

        # Print summary
        print(f"\nScraped {len(products)} products")

        # Print sample product
        if products:
            print("\nSample product:")
            sample = products[0]
            print(f"Title: {sample.get('title', 'N/A')}")
            print(f"Link: {sample.get('url', 'N/A')}")
            print(f"Price: {sample.get('price', 'N/A')}")
            print(f"Rating: {sample.get('rating', 'N/A')}")

    finally:
        scraper.close()

if __name__ == "__main__":
    main()
