#!/usr/bin/env python3
"""
Script to fix broken Amazon affiliate links by generating fresh ones using the scraper
"""

import re
from bs4 import BeautifulSoup
from amazon_scraper import AmazonScraper


def fix_broken_amazon_links(html_file_path, affiliate_id="cyberheroes-20"):
    """
    Fix broken Amazon affiliate links by generating fresh working ones

    Args:
        html_file_path: Path to the HTML file
        affiliate_id: Amazon affiliate ID to use
    """
    # Read the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')

    # Find all Amazon links
    amazon_links = soup.find_all('a', href=re.compile(r'https://www\.amazon\.com/'))

    print(f"Found {len(amazon_links)} Amazon links to fix")

    scraper = AmazonScraper(use_selenium=False, headless=True, affiliate_id=affiliate_id)

    for link in amazon_links:
        original_url = link['href']

        # Extract ASIN from the broken URL
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', original_url)
        if asin_match:
            asin = asin_match.group(1)

            # Get product name from link context
            product_name = get_product_name_from_context(link)

            # Generate fresh affiliate URL
            fresh_affiliate_url = generate_fresh_affiliate_url(scraper, asin, product_name, affiliate_id)

            if fresh_affiliate_url:
                link['href'] = fresh_affiliate_url
                print(f"Fixed: {original_url}")
                print(f"    -> {fresh_affiliate_url}\n")

    scraper.close()

    # Write back to file
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print(f"✅ Successfully fixed {len(amazon_links)} Amazon links with fresh affiliate URLs")


def create_url_slug(product_name):
    """Create URL slug from product name (for cosmetic readability in the URL)."""
    slug = re.sub(r'[^\w\s-]', '', product_name)
    slug = re.sub(r'[\s]+', '-', slug)
    return slug.strip('-')


def get_product_name_from_context(link_element):
    """Extract product name from the link's context"""
    link_text = link_element.get_text().strip()
    if link_text:
        return link_text

    parent_h3 = link_element.find_parent('h3')
    if parent_h3:
        return parent_h3.get_text().strip()

    return "product"


def generate_fresh_affiliate_url(scraper, asin, product_name, affiliate_id):
    """Generate a fresh affiliate URL"""
    try:
        slug = create_url_slug(product_name)
        base_url = f"https://www.amazon.com/{slug}/dp/{asin}"
        return f"{base_url}?tag={affiliate_id}"
    except Exception as e:
        print(f"Error generating affiliate URL: {e}")
        return None


if __name__ == "__main__":
    fix_broken_amazon_links("seo_article.html")
