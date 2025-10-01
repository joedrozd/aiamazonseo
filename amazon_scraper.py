#!/usr/bin/env python3
"""
Amazon Product Scraper

Scrapes Amazon products based on keywords, extracting title, price, rating, reviews, image, and ASIN.
Generates clean affiliate links.
Handles dynamic content using Selenium.
"""

import requests
import time
import random
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode, urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import re
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AmazonScraper:
    """Amazon product scraper with keyword-based search and affiliate link generation."""

    def __init__(self, use_selenium: bool = False, headless: bool = True, affiliate_id: str = "cyberheroes-20"):
        self.use_selenium = use_selenium
        self.headless = headless
        self.affiliate_id = affiliate_id
        self.session = requests.Session()
        self.driver = None
        self.base_url = "https://www.amazon.com"
        self.search_url = "https://www.amazon.com/s"

        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

        self.min_delay = 1.0
        self.max_delay = 3.0
        self.last_request_time = 0

        if self.use_selenium:
            self._init_selenium()

    def _init_selenium(self):
        try:
            options = Options()
            if self.headless:
                options.add_argument('--headless')  # Revert to standard headless for compatibility
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # Try multiple approaches to get the correct Chrome driver
            try:
                # First try with explicit platform and version specification
                driver_path = ChromeDriverManager(platform="win64", driver_version="130.0.6723.69").install()
            except:
                try:
                    # Fallback to standard installation
                    driver_path = ChromeDriverManager().install()
                except:
                    # Last resort - try a known working version
                    driver_path = ChromeDriverManager(driver_version="130.0.6723.69").install()

            service = webdriver.ChromeService(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Selenium WebDriver initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False

    def _get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            sleep_time = random.uniform(self.min_delay, self.max_delay)
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _add_affiliate_tag(self, url: str) -> str:
        if not url or not self.affiliate_id:
            return url
        parsed = urlparse(url)
        clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return f"{clean_url}?tag={self.affiliate_id}"

    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
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
            full_url = f"{url}?{urlencode(params)}" if params else url
            response = self.session.get(full_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def _selenium_get_page(self, url: str) -> Optional[str]:
        if not self.driver:
            return None
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
            )
            time.sleep(2)
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Selenium request failed: {e}")
            return None

    def _extract_product_data(self, product_element) -> Optional[Dict[str, Any]]:
        try:
            product_data = {}

            # Title - Try multiple selectors for better compatibility
            title_elem = None
            title_selectors = [
                'h2 a.a-link-normal',
                'h2 a[href*="dp/"]',
                '.a-text-normal',
                '.a-color-base.a-text-normal',
                '.a-size-medium.a-color-base.a-text-normal'
            ]

            for selector in title_selectors:
                title_elem = product_element.select_one(selector)
                if title_elem and title_elem.get_text().strip():
                    break

            product_data['title'] = title_elem.get_text().strip() if title_elem else None

            # URL - Extract from the title element or search within the product
            raw_url = None
            if title_elem and 'href' in title_elem.attrs:
                raw_url = urljoin(self.base_url, title_elem['href'])
            else:
                # Fallback: look for any link with dp/ (product detail page)
                link_elem = product_element.find('a', href=re.compile(r'/dp/'))
                if link_elem:
                    raw_url = urljoin(self.base_url, link_elem['href'])

            product_data['url'] = self._add_affiliate_tag(raw_url) if raw_url else None

            # Price - Try multiple selectors
            price_elem = None
            price_selectors = [
                'span.a-price .a-offscreen',
                'span.a-price-whole',
                'span.a-color-price',
                '.a-price .a-offscreen'
            ]

            for selector in price_selectors:
                price_elem = product_element.select_one(selector)
                if price_elem and price_elem.get_text().strip():
                    break

            if price_elem:
                price_text = re.sub(r'[^\d.]', '', price_elem.get_text())
                product_data['price'] = price_text if price_text else None
            else:
                product_data['price'] = None

            # Rating - Try multiple selectors
            rating_elem = None
            rating_selectors = [
                'span.a-icon-alt',
                'i.a-icon-star-small span',
                '.a-icon-alt',
                'span[aria-label*="out of 5 stars"]'
            ]

            for selector in rating_selectors:
                rating_elem = product_element.select_one(selector)
                if rating_elem:
                    break

            if rating_elem:
                rating_match = re.search(r'(\d+\.?\d*)', rating_elem.get_text())
                product_data['rating'] = float(rating_match.group(1)) if rating_match else None
            else:
                product_data['rating'] = None

            # Reviews count - Try multiple selectors
            reviews_elem = None
            reviews_selectors = [
                'span.a-size-base',
                '.a-size-small',
                'span[aria-label*="ratings"]',
                'a[href*="review"] span'
            ]

            for selector in reviews_selectors:
                reviews_elem = product_element.select_one(selector)
                if reviews_elem:
                    break

            if reviews_elem:
                reviews_match = re.search(r'\d+(?:,\d+)*', reviews_elem.get_text())
                product_data['reviews_count'] = int(reviews_match.group(0).replace(',', '')) if reviews_match else None
            else:
                product_data['reviews_count'] = None

            # Image - Try multiple selectors
            img_elem = None
            img_selectors = [
                'img.s-image',
                'img[data-image-index]',
                '.s-image',
                'img[src*="media-amazon.com"]'
            ]

            for selector in img_selectors:
                img_elem = product_element.select_one(selector)
                if img_elem and 'src' in img_elem.attrs:
                    break

            product_data['image_url'] = img_elem['src'] if img_elem and 'src' in img_elem.attrs else None

            # ASIN - Extract from URL or data-asin attribute
            if product_data['url']:
                asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_data['url'])
                product_data['asin'] = asin_match.group(1) if asin_match else None
            else:
                # Try to get ASIN from data-asin attribute
                asin_elem = product_element.get('data-asin') or product_element.find(attrs={'data-asin': True})
                product_data['asin'] = asin_elem.get('data-asin') if asin_elem else None

            return product_data
        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None

    def search_products(self, keywords: List[str], max_pages: int = 3, max_products: int = 50) -> List[Dict[str, Any]]:
        all_products = []
        for keyword in keywords:
            logger.info(f"Searching for keyword: {keyword}")
            for page in range(1, max_pages + 1):
                if len(all_products) >= max_products:
                    break
                params = {'k': keyword, 'page': page, 'ref': f'sr_pg_{page}'}
                html = self._selenium_get_page(f"{self.search_url}?{urlencode(params)}") if self.use_selenium else self._make_request(self.search_url, params)
                if not html:
                    continue
                soup = BeautifulSoup(html, 'lxml')
                products = soup.find_all('div', {'data-component-type': 's-search-result'})
                if not products:
                    products = soup.find_all('div', class_='s-result-item')
                logger.info(f"Found {len(products)} products on page {page}")
                for product in products:
                    if len(all_products) >= max_products:
                        break
                    data = self._extract_product_data(product)
                    if data and data['title']:
                        data['search_keyword'] = keyword
                        all_products.append(data)
                next_page = soup.find('a', {'aria-label': 'Go to next page'})
                if not next_page:
                    break
                time.sleep(random.uniform(1.0, 2.0))
            if len(all_products) >= max_products:
                break
        logger.info(f"Total products scraped: {len(all_products)}")
        return all_products

    def save_to_json(self, products: List[Dict[str, Any]], filename: str):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            logger.info(f"Products saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save products: {e}")

    def save_product_links(self, products: List[Dict[str, Any]], filename: str, format: str = 'txt'):
        try:
            if format.lower() == 'csv':
                import csv
                with open(f"{filename}.csv", 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Title', 'URL', 'Price', 'Rating', 'Search Keyword'])
                    for p in products:
                        writer.writerow([p.get('title'), p.get('url'), p.get('price'), p.get('rating'), p.get('search_keyword')])
            else:
                with open(f"{filename}.txt", 'w', encoding='utf-8') as f:
                    f.write("AMAZON PRODUCT LINKS\n")
                    f.write("="*50+"\n\n")
                    for i, p in enumerate(products, 1):
                        f.write(f"{i}. {p.get('title')}\n")
                        f.write(f"   Link: {p.get('url')}\n")
                        f.write(f"   Price: {p.get('price')}\n")
                        f.write(f"   Rating: {p.get('rating')}\n")
                        f.write(f"   Keyword: {p.get('search_keyword')}\n")
                        f.write("-"*50+"\n\n")
        except Exception as e:
            logger.error(f"Failed to save links: {e}")

    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver closed")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Amazon Product Scraper')
    parser.add_argument('--keywords', nargs='+', required=True, help='Keywords to search for')
    parser.add_argument('--max-pages', type=int, default=3, help='Max pages per keyword')
    parser.add_argument('--max-products', type=int, default=50, help='Max products')
    parser.add_argument('--output', default='amazon_products', help='Output filename without extension')
    parser.add_argument('--format', choices=['json', 'txt', 'csv', 'all'], default='all')
    parser.add_argument('--selenium', action='store_true', help='Use Selenium')
    parser.add_argument('--headless', action='store_true', default=True, help='Headless mode (Selenium)')
    parser.add_argument('--affiliate-id', default='cyberheroes-20', help='Affiliate ID')
    args = parser.parse_args()

    scraper = AmazonScraper(use_selenium=args.selenium, headless=args.headless, affiliate_id=args.affiliate_id)
    try:
        products = scraper.search_products(args.keywords, args.max_pages, args.max_products)
        if args.format in ['json', 'all']:
            scraper.save_to_json(products, f"{args.output}.json")
        if args.format in ['txt', 'all']:
            scraper.save_product_links(products, args.output, format='txt')
        if args.format in ['csv', 'all']:
            scraper.save_product_links(products, args.output, format='csv')
        print(f"Scraped {len(products)} products.")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
