#!/usr/bin/env python3
"""
AI Amazon SEO Article Generator

Workflow:
1. Send prompt to API to get relevant SEO keywords
2. Use keywords to scrape Amazon products
3. Send products back to API to generate HTML article content
4. Save article to text file
"""

import requests
import json
import sys
import logging
from typing import List, Dict, Any, Optional
from amazon_scraper import AmazonScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SEOArticleGenerator:
    """
    Main class for generating SEO articles from prompts using Amazon product data.
    """

    def __init__(self, api_url: str = "http://localhost:1234/v1/chat/completions"):
        """
        Initialize the article generator.

        Args:
            api_url: URL of the chat completions API
        """
        self.api_url = api_url
        self.session = requests.Session()

    def send_chat_request(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Send a chat request to the API service.

        Args:
            prompt: The prompt to send

        Returns:
            Response data as dictionary, or None if failed
        """
        try:
            payload = {"messages": [{"role": "user", "content": prompt}]}

            logger.info(f"Sending request to {self.api_url}")
            print(f"⏳ Generating response (this may take 5-10 minutes)...")
            response = self.session.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5000.0 
            )

            response.raise_for_status()
            response_data = response.json()

            logger.info("API request successful")
            return response_data

        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to API at {self.api_url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"API returned status {e.response.status_code}: {e.response.text}")
            return None
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from API")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def extract_keywords_from_prompt(self, prompt: str) -> List[str]:
        """
        Send prompt to API to extract relevant SEO keywords.

        Args:
            prompt: The original user prompt

        Returns:
            List of SEO keywords
        """
        keyword_prompt = f"""
        Based on this prompt: "{prompt}"

        Generate a list of 5-10 relevant SEO keywords that would be good for Amazon product searches.
        Focus on specific, searchable terms that people might use when looking for products.

        Return only a JSON array of strings, like: ["keyword1", "keyword2", "keyword3"]
        Make sure the JSON is complete and properly formatted.
        """

        logger.info("Requesting SEO keywords from API")
        response = self.send_chat_request(keyword_prompt)

        if not response:
            logger.error("Failed to get keywords from API")
            return []

        try:
            # Extract the response content
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '').strip()

            # Clean up the content - remove any markdown formatting
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            logger.debug(f"Raw API response content: {content}")

            # Try to parse as JSON
            keywords = json.loads(content)

            if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
                logger.info(f"Extracted {len(keywords)} keywords: {keywords}")
                return keywords
            else:
                logger.error("API response is not a valid keyword list")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response as JSON: {e}")
            logger.error(f"Raw content: {content}")

            # Try to extract keywords from incomplete JSON
            return self._extract_keywords_from_incomplete_json(content)

    def _extract_keywords_from_incomplete_json(self, content: str) -> List[str]:
        """
        Attempt to extract keywords from incomplete or malformed JSON response.

        Args:
            content: The raw API response content

        Returns:
            List of extracted keywords
        """
        import re

        logger.info("Attempting to extract keywords from incomplete JSON")

        # Look for JSON array pattern
        array_match = re.search(r'\[([^\]]*)\]', content)
        if array_match:
            array_content = array_match.group(1)

            # Split by commas and extract quoted strings
            items = []
            current_item = ""
            in_quotes = False
            quote_char = None

            for char in array_content:
                if not in_quotes and char in ['"', "'"]:
                    in_quotes = True
                    quote_char = char
                    current_item += char
                elif in_quotes and char == quote_char:
                    in_quotes = False
                    current_item += char
                    items.append(current_item)
                    current_item = ""
                elif in_quotes:
                    current_item += char
                elif char == ',' and not in_quotes:
                    if current_item.strip():
                        items.append(current_item.strip())
                    current_item = ""

            # Add the last item if exists
            if current_item.strip():
                items.append(current_item.strip())

            # Clean up the items - remove quotes and whitespace
            keywords = []
            for item in items:
                item = item.strip()
                if item.startswith('"') and item.endswith('"'):
                    item = item[1:-1]
                elif item.startswith("'") and item.endswith("'"):
                    item = item[1:-1]
                if item and len(item) > 2:  # Filter out very short items
                    keywords.append(item)

            if keywords:
                logger.info(f"Extracted {len(keywords)} keywords from incomplete JSON: {keywords}")
                return keywords

        # Fallback: try to extract quoted strings from the entire content
        quoted_strings = re.findall(r'["\']([^"\']+)["\']', content)
        if quoted_strings:
            # Filter out very short strings and duplicates
            keywords = list(set([s.strip() for s in quoted_strings if len(s.strip()) > 3]))
            if keywords:
                logger.info(f"Extracted {len(keywords)} keywords from quoted strings: {keywords}")
                return keywords[:10]  # Limit to 10 keywords

        logger.error("Could not extract any keywords from the response")
        return []

    def scrape_products_from_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Use Amazon scraper to get products for the given keywords.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of product dictionaries
        """
        logger.info(f"Starting product scraping for {len(keywords)} keywords")

        scraper = AmazonScraper(use_selenium=False, headless=True)

        try:
            products = scraper.search_products(
                keywords=keywords,
                max_pages=2,  # Limit pages for faster processing
                max_products=20  # Limit products per keyword
            )

            logger.info(f"Successfully scraped {len(products)} products")
            return products

        except Exception as e:
            logger.error(f"Error during product scraping: {str(e)}")
            return []
        finally:
            scraper.close()

    def generate_article_html(self, prompt: str, products: List[Dict[str, Any]]) -> Optional[str]:
        """
        Send products to API to generate HTML article content.

        Args:
            prompt: Original user prompt
            products: List of scraped products

        Returns:
            Generated HTML article content
        """
        # Format products for the API with full affiliate URLs
        products_text = "\n".join([
            f"- {p.get('title', 'N/A')} (Price: {p.get('price', 'N/A')}, Rating: {p.get('rating', 'N/A')}, URL: {p.get('url', 'N/A')}, Search Keyword: {p.get('search_keyword', 'N/A')})"
            for p in products[:10]  # Limit to first 10 products
        ])

        article_prompt = f"""
        Original prompt: "{prompt}"

        Available Amazon products:
        {products_text}

        Generate an SEO-optimized article in HTML format. Use proper HTML tags like:
        - <h1> for main title
        - <h2>, <h3> for section headings
        - <p> for paragraphs
        - <a> for links (use the product URLs)
        - <ul>/<li> for lists
        - <strong> or <em> for emphasis

        Make the article informative, engaging, and naturally incorporate the product links.
        Focus on providing value while including affiliate product recommendations.

        Return only the HTML content, no markdown or code blocks.

        Please ensure the HTML is well-formed and complete.

        Make the word count between 800-1500 words.
        Do not include any disclaimers or notes about affiliate links.
        Use a friendly and conversational tone.

        Example structure:
        <h1>Main Title</h1>     
        <p>Introductory paragraph...</p>
        <h2>Section Heading</h2>
        <p>Content...</p>

        <h3>Subsection Heading</h3>
        <p>More content...</p>
        <ul>
            <li><a href="product_link_1">Product 1</a> - brief description</li>
            <li><a href="product_link_2">Product 2</a> - brief description</li>
            ...
        </ul>
        <p>Conclusion paragraph...</p>

        
        Ensure the HTML is valid and can be directly used in a blog post.
        Return only the HTML Body content, nothing else.
        """

        logger.info("Requesting HTML article generation from API")
        response = self.send_chat_request(article_prompt)

        if not response:
            logger.error("Failed to generate article from API")
            return None

        try:
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            logger.info("Successfully generated HTML article")
            return content.strip()

        except Exception as e:
            logger.error(f"Error extracting article content: {str(e)}")
            return None

    def save_article_to_file(self, content: str, filename: str = "seo_article.html") -> bool:
        """
        Save the generated article to a text file.

        Args:
            content: Article content to save
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Article saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save article to file: {str(e)}")
            return False

    def generate_article(self, prompt: str) -> bool:
        """
        Execute the complete article generation workflow.

        Args:
            prompt: The user's prompt

        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting article generation workflow")
        logger.info(f"Prompt: {prompt}")

        print("🚀 Starting article generation workflow...")
        print(f"📝 Prompt: {prompt}")
        print()

        # Step 1: Extract SEO keywords
        print("🔍 Step 1/4: Extracting SEO keywords from prompt...")
        keywords = self.extract_keywords_from_prompt(prompt)
        if not keywords:
            print("❌ Failed to extract keywords")
            logger.error("No keywords extracted, aborting")
            return False
        print(f"✅ Found {len(keywords)} keywords: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}")
        print()

        # Step 2: Scrape products
        print("🛒 Step 2/4: Scraping Amazon products...")
        products = self.scrape_products_from_keywords(keywords)
        if not products:
            print("❌ Failed to scrape products")
            logger.error("No products scraped, aborting")
            return False
        print(f"✅ Scraped {len(products)} products from Amazon")
        print()

        # Step 3: Generate HTML article
        print("✍️  Step 3/4: Generating HTML article content...")
        article_html = self.generate_article_html(prompt, products)
        if not article_html:
            print("❌ Failed to generate article HTML")
            logger.error("Failed to generate article HTML, aborting")
            return False
        print("✅ Article HTML generated successfully")
        print()

        # Step 4: Save to file
        print("💾 Step 4/4: Saving article to file...")
        success = self.save_article_to_file(article_html)
        if success:
            print("✅ Article saved successfully")
            logger.info("Article generation workflow completed successfully")
        else:
            print("❌ Failed to save article")
            logger.error("Failed to save article to file")

        return success

def main():
    """Main function that runs when the script is executed."""
    import argparse

    parser = argparse.ArgumentParser(description='AI Amazon SEO Article Generator')
    parser.add_argument('prompt', help='The prompt to generate an article from')
    parser.add_argument('--api-url', default='http://localhost:1234/v1/chat/completions',
                       help='API endpoint URL (default: http://localhost:1234/v1/chat/completions)')
    parser.add_argument('--output', default='seo_article.txt',
                       help='Output filename (default: seo_article.txt)')

    args = parser.parse_args()

    print("🤖 AI Amazon SEO Article Generator")
    print("=" * 50)

    # Initialize generator
    generator = SEOArticleGenerator(api_url=args.api_url)

    # Generate article
    success = generator.generate_article(args.prompt)

    if success:
        print(f"✅ Article generated successfully and saved to {args.output}")
    else:
        print("❌ Article generation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
