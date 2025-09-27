import requests
import re
from urllib.parse import urlparse, parse_qs
import time

def check_amazon_link(url):
    """Check if an Amazon URL returns a 404 error"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # First try a HEAD request (faster)
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)

        if response.status_code == 404:
            return False, "404 Not Found"
        elif response.status_code == 200:
            return True, "OK"
        else:
            # If HEAD doesn't work, try GET
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            if response.status_code == 404:
                return False, "404 Not Found"
            elif response.status_code == 200:
                return True, "OK"
            else:
                return False, f"Status code: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"

def extract_asin_from_url(url):
    """Extract ASIN from Amazon URL"""
    # Look for ASIN in URL path
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)

    # Look for ASIN in product-reviews URL
    match = re.search(r'/product-reviews/([A-Z0-9]{10})', url)
    if match:
        return match.group(1)

    return None

def generate_amazon_search_url(product_name):
    """Generate Amazon search URL for a product"""
    # Clean up product name for URL
    search_term = product_name.replace(' ', '+').replace('&', 'and')
    return f"https://www.amazon.com/s?k={search_term}&ref=sr_pg_1"

def check_all_links():
    """Check all Amazon links in the HTML file"""
    links_to_check = [
        {
            "name": "DIERYA T68SE",
            "url": "https://www.amazon.com/DIERYA-T68SE-Mechanical-Ultra-Compact-Stand-Alone/dp/B0BGXZF1MD?dib=eyJ2IjoiMSJ9.Sm8_Tq-YfUxzvAetb-bhqohpeZKhtcxzqKnnwaNfKKrgHRRlAnxfpMAlbaoo9eKCT14nYe-x7l0WIribfWasmrgiGbPh9TEih17cR9TuuQw.3LHf1ruXzFWJYzWJ_Lru38AzgDhlsQdlEFSOU5k5y8g&dib_tag=se&keywords=dierya-t68se-60-gaming-mechanical-keyboard&qid=1758683110&sr=8-1&th=1&linkCode=ll1&tag=joed05-20&linkId=fa11d325ba2ac1e035100f8f9f285e01&language=en_US&ref_=as_li_ss_tl"
        },
        {
            "name": "Redragon K742",
            "url": "https://www.amazon.com/Redragon-K742-Mechanical-Gaming-Keyboard/dp/B08XKQZ9V3?dib=eyJ2IjoiMSJ9.8m9_Tq-YfUxzvAetb-bhqohpeZKhtcxzqKnnwaNfKKrgHRRlAnxfpMAlbaoo9eKCT14nYe-x7l0WIribfWasmrgiGbPh9TEih17cR9TuuQw.4LHf1ruXzFWJYzWJ_Lru38AzgDhlsQdlEFSOU5k5y8g&dib_tag=se&keywords=redragon-k742-wireless-mechanical-gaming-keyboard&qid=1758683111&sr=8-2&th=1&linkCode=ll1&tag=joed05-20&linkId=fb11d325ba2ac1e035100f8f9f285e02&language=en_US&ref_=as_li_ss_tl"
        },
        {
            "name": "CHERRY MX Board 3.0 S",
            "url": "https://www.amazon.com/Cherry-Mechanical-Keyboard-Aluminum-Housing/dp/B0D8RTKHZ9?dib=eyJ2IjoiMSJ9.GyJiDykdnBpPXebuDXyw1zGTxkSRcuFF0X9GicctiZsHszvViw18nHLgpg5XZ4NZUHQVyobJG98e1h4BjaIuqJiVn6s0R0tHP5klRWKVt7c.xOenFp5C8IjOmrS5EeeXv6Mh1qyv9xvadXKOyDk43Uc&dib_tag=se&keywords=CHERRY-MX-Board-3-0S-Mechanical&qid=1758683304&sr=8-3&th=1&linkCode=ll1&tag=cyberheroes-20&linkId=c50d323f3ce21d6d5d848026435d01b2&language=en_US&ref_=as_li_ss_tl"
        },
        {
            "name": "AUSDOM 98Pro",
            "url": "https://www.amazon.com/AUSDOM-98Pro-Mechanical-Keyboard-Switches/dp/B086G4W1XZ?dib=eyJ2IjoiMSJ9.0o1_Tq-YfUxzvAetb-bhqohpeZKhtcxzqKnnwaNfKKrgHRRlAnxfpMAlbaoo9eKCT14nYe-x7l0WIribfWasmrgiGbPh9TEih17cR9TuuQw.6NHf1ruXzFWJYzWJ_Lru38AzgDhlsQdlEFSOU5k5y8g&dib_tag=se&keywords=ausdom-98pro-silent-mechanical-keyboard&qid=1758683113&sr=8-4&th=1&linkCode=ll1&tag=joed05-20&linkId=fd11d325ba2ac1e035100f8f9f285e04&language=en_US&ref_=as_li_ss_tl"
        },
        {
            "name": "Cherry KC 200",
            "url": "https://www.amazon.com/Cherry-KC-200-Mechanical-Keyboard/dp/B07Y8PZJ6D?dib=eyJ2IjoiMSJ9.1p2_Tq-YfUxzvAetb-bhqohpeZKhtcxzqKnnwaNfKKrgHRRlAnxfpMAlbaoo9eKCT14nYe-x7l0WIribfWasmrgiGbPh9TEih17cR9TuuQw.7OHf1ruXzFWJYzWJ_Lru38AzgDhlsQdlEFSOU5k5y8g&dib_tag=se&keywords=cherry-kc-200-mx-mechanical-office-keyboard&qid=1758683114&sr=8-5&th=1&linkCode=ll1&tag=joed05-20&linkId=fe11d325ba2ac1e035100f8f9f285e05&language=en_US&ref_=as_li_ss_tl"
        },
        {
            "name": "EPOMAKER TH99",
            "url": "https://www.amazon.com/EPOMAKER-TH99-Mechanical-Keyboard-Switches/dp/B0857K4Y6N?dib=eyJ2IjoiMSJ9.2q3_Tq-YfUxzvAetb-bhqohpeZKhtcxzqKnnwaNfKKrgHRRlAnxfpMAlbaoo9eKCT14nYe-x7l0WIribfWasmrgiGbPh9TEih17cR9TuuQw.8PHf1ruXzFWJYzWJ_Lru38AzgDhlsQdlEFSOU5k5y8g&dib_tag=se&keywords=epomaker-th99-wireless-mechanical-keyboard&qid=1758683115&sr=8-6&th=1&linkCode=ll1&tag=joed05-20&linkId=ff11d325ba2ac1e035100f8f9f285e06&language=en_US&ref_=as_li_ss_tl"
        }
    ]

    print("Checking Amazon links for 404 errors...")
    print("=" * 50)

    failed_links = []

    for link in links_to_check:
        print(f"Checking {link['name']}...")
        is_valid, status = check_amazon_link(link['url'])

        if is_valid:
            print(f"  ✓ {link['name']}: {status}")
        else:
            print(f"  ✗ {link['name']}: {status}")
            asin = extract_asin_from_url(link['url'])
            failed_links.append({
                "name": link['name'],
                "url": link['url'],
                "status": status,
                "asin": asin
            })

        # Be respectful to Amazon's servers
        time.sleep(1)

    print("\n" + "=" * 50)
    if failed_links:
        print(f"Found {len(failed_links)} links with issues:")
        for failed in failed_links:
            print(f"- {failed['name']}: {failed['status']}")
            if failed['asin']:
                print(f"  ASIN: {failed['asin']}")
                search_url = generate_amazon_search_url(failed['name'])
                print(f"  Search URL: {search_url}")
            print()
    else:
        print("All links are working correctly!")

    return failed_links

if __name__ == "__main__":
    failed_links = check_all_links()
