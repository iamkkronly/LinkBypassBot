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
        return

    soup = BeautifulSoup(response.content, 'lxml')

    # Locate the download links
    # Based on the HTML structure seen:
    # <h3><a href="...">480p...</a></h3>
    # <h4><a href="...">720p...</a></h4>
    # They seem to be in h3 or h4 tags, and the text contains the quality.

    links = []

    # We look for all 'a' tags
    for a_tag in soup.find_all('a', href=True):
        text = a_tag.get_text().strip()
        href = a_tag['href']

        # Filter for quality indicators
        if any(q in text.lower() for q in ['480p', '720p', '1080p']):
            # Filter out some unrelated links if necessary (like "Watch Online" if not desired, but user asked for download links)
            # The structure showed links like "480p⚡[500MB]" or "720p 10bit HEVC [910MB]"

            # We want to avoid category links like "720p Movies" in the footer/sidebar if they exist
            # The download links in the example were inside h3/h4 tags with style="text-align: center;"

            # Let's check if the parent is a header tag or p tag which is common for these sites
            parent = a_tag.parent
            if parent.name in ['h2', 'h3', 'h4', 'p', 'strong', 'em']:
                 links.append({'text': text, 'link': href})

    if not links:
        print("No download links found.")
        return

    print(f"Found {len(links)} links:")
    for link in links:
        print(f"{link['text']}: {link['link']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter Hdhub4u movie link: ")

    scrape_hdhub4u(url)
