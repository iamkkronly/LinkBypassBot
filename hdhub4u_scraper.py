import requests
from bs4 import BeautifulSoup
import sys

def scrape_hdhub4u(url):
    print(f"Scraping {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []

    # Try lxml first, fallback to html.parser if it fails (e.g. malformed HTML)
    try:
        soup = BeautifulSoup(response.content, 'lxml')
    except Exception as e:
        print(f"lxml parsing failed ({e}). Falling back to html.parser.")
        soup = BeautifulSoup(response.content, 'html.parser')

    links = []

    # We look for all 'a' tags
    for a_tag in soup.find_all('a', href=True):
        text = a_tag.get_text().strip()
        href = a_tag['href']

        # Filter for quality indicators
        if any(q in text.lower() for q in ['480p', '720p', '1080p', 'episode']):
            parent = a_tag.parent
            valid_parents = ['h2', 'h3', 'h4', 'p', 'strong', 'em']
            if parent.name in valid_parents:
                 links.append({'text': text, 'link': href})
            elif parent.name == 'span' and parent.parent and parent.parent.name in valid_parents:
                 links.append({'text': text, 'link': href})

    if not links:
        print("No download links found.")
        return []

    return links

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        # Default link as requested
        user_input = "https://hdhub4u.rehab/bigg-boss-season-19-hindi-webrip-all-episodes/"

    links = scrape_hdhub4u(user_input)
    if links:
        print(f"Found {len(links)} links:")
        for link in links:
            print(f"{link['text']}: {link['link']}")
