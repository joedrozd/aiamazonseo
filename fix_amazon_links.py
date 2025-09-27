from bs4 import BeautifulSoup, NavigableString

PRODUCTS = {
    "Dell XPS 15": "B09JQHZ7X6",
    "MacBook Pro (16-inch)": "B09JQK3K48",
    "Lenovo ThinkPad X1 Carbon Gen 10": "B09Y2S8VQH",
    "HP Spectre x360 14": "B09MRYJ1K5"
}

AMAZON_DOMAIN = "https://www.amazon.com"
AFFILIATE_TAG = "cyberheroes-20"

def add_affiliate_links(html_file_path, output_file_path):
    with open(html_file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    for product_name, asin in PRODUCTS.items():
        for text_node in soup.find_all(string=lambda text: text and product_name in text):
            parent = text_node.parent
            new_tag = soup.new_tag("a", href=f"{AMAZON_DOMAIN}/dp/{asin}?tag={AFFILIATE_TAG}", target="_blank")
            new_tag.string = product_name

            split_text = str(text_node).split(product_name, 1)
            new_nodes = []
            if split_text[0]:
                new_nodes.append(NavigableString(split_text[0]))
            new_nodes.append(new_tag)
            if split_text[1]:
                new_nodes.append(NavigableString(split_text[1]))

            # Replace the old text node with new nodes
            text_node.replace_with(new_nodes[0])
            last_node = new_nodes[0]
            for node in new_nodes[1:]:
                last_node.insert_after(node)
                last_node = node

    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print(f"✅ Affiliate links fixed and saved to {output_file_path}")


if __name__ == "__main__":
    add_affiliate_links("seo_article.html", "article_aff.html")
