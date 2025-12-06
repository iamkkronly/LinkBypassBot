import requests
import re
import base64
import json
import codecs
from bs4 import BeautifulSoup
import sys
import time
from urllib.parse import urljoin

# Constants
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def rot13(s):
    return codecs.encode(s, 'rot_13')

def decode_gadgetsweb_payload(o_val):
    """
    Decodes the 'o' payload from gadgetsweb.xyz/hblinks.dad redirector.
    Logic: Base64 -> Base64 -> ROT13 -> Base64 -> JSON
    """
    try:
        # 1st decode
        d1 = base64.b64decode(o_val).decode('utf-8')

        # 2nd decode
        d2 = base64.b64decode(d1).decode('utf-8')

        # ROT13
        d3 = rot13(d2)

        # 3rd decode (Base64)
        d4 = base64.b64decode(d3).decode('utf-8')

        # JSON Parse
        data = json.loads(d4)
        return data
    except Exception as e:
        print(f"Error decoding payload: {e}")
        return None

def bypass_gadgetsweb(url):
    """
    Bypasses gadgetsweb.xyz to get the final hblinks.dad URL.
    """
    print(f"Bypassing {url}...")
    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Extract 'o' value
        # Pattern: s('o','BASE64_STRING',...)
        match = re.search(r"s\('o','([^']+)'", response.text)
        if not match:
            print("Could not find payload 'o' in the page.")
            # It might be that the URL is already hblinks.dad or another page?
            if "hblinks.dad" in response.url:
                return response.url
            return None

        o_val = match.group(1)
        # print(f"Found payload: {o_val[:20]}...")

        data = decode_gadgetsweb_payload(o_val)
        if data and 'o' in data:
            final_url_b64 = data['o']
            final_url = base64.b64decode(final_url_b64).decode('utf-8')
            return final_url
        else:
            print("Failed to extract destination URL from payload.")
            return None

    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return None

def scrape_hblinks_page(url, visited=None):
    """
    Scrapes a single hblinks.dad page for download links and navigation.
    """
    if visited is None:
        visited = set()

    if url in visited:
        return None, [], []

    visited.add(url)

    print(f"Scraping {url}...")
    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        # Extract Title
        title_tag = soup.find('h1', class_='entry-title')
        title = title_tag.get_text().strip() if title_tag else "Unknown Title"

        # Extract Download Links
        # They are usually inside <div style="text-align: center;"> <p><a><img .../></a></p> ...
        # Or just look for known domains in 'a' tags.

        download_links = []
        known_domains = ["hubcloud", "hubdrive", "gofile", "katfile", "drivehub", "gdflix"]

        for a in soup.find_all('a', href=True):
            href = a['href']
            # Simple check for download domains
            if any(domain in href for domain in known_domains):
                # Try to get text or image alt
                link_text = a.get_text().strip()
                if not link_text:
                    img = a.find('img')
                    if img and img.get('src'):
                        # Use image filename as hint or verify based on domain
                        if "Cloud-Logo" in img['src']: link_text = "HubCloud"
                        elif "Hubdrive" in img['src']: link_text = "HubDrive"
                        elif "gofile" in img['src']: link_text = "GoFile"
                        else: link_text = "Download"

                download_links.append({'text': link_text or "Download", 'link': href})

        # Extract Navigation Links (Previous/Next)
        nav_links = []
        nav_div = soup.find('div', class_='nav-links')
        if nav_div:
            for a in nav_div.find_all('a', href=True):
                nav_text = a.get_text().strip()
                # Check if it's relevant (e.g. contains 480p, 720p, 1080p)
                # Usually navigation text is like "Previous post: Kuttram ... 720p Pack"
                # But sometimes "Previous" is in span, and title is in another span.

                # Let's trust the href and maybe fetch title from it later or use the link text as hint
                nav_links.append({'text': nav_text, 'link': a['href']})

        return title, download_links, nav_links

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None, [], []

def main(url):
    # Step 1: Resolve initial URL
    if "gadgetsweb.xyz" in url:
        target_url = bypass_gadgetsweb(url)
        if not target_url:
            print("Failed to bypass gadgetsweb.")
            return
        print(f"Resolved to: {target_url}")
    else:
        target_url = url

    # Step 2: Scrape the resolved page
    # We want to find all qualities.
    # Strategy: Scrape current page. Check "Previous/Next".
    # If they look like same content but different quality, visit them.

    visited = set()
    queue = [target_url]

    # We want to group by quality
    results = {}

    # We will limit recursion depth/breadth to avoid infinite crawling
    # For now, just checking immediate neighbors (depth 1 or 2) is probably enough if they are linked sequentially.
    # But usually it's [720p Pack] -> [480p Pack] -> etc.

    processed_count = 0
    max_pages = 5 # Safety limit

    while queue and processed_count < max_pages:
        current_url = queue.pop(0)
        if current_url in visited:
            continue

        title, links, nav = scrape_hblinks_page(current_url, visited)

        if title:
            print(f"Found Page: {title}")
            results[title] = links

            # Heuristic to find related quality pages:
            # Check if title shares similarity with original title
            # For simplicity, we just add all nav links to queue if not visited
            # But we should prioritize or filter.

            base_title_words = title.split()
            # Simple check: if > 50% words match

            for n in nav:
                # n['text'] often contains "Previous/Next post: Title"
                # We add to queue
                if n['link'] not in visited and n['link'] not in queue:
                     # Maybe check if it's the same series/movie?
                     # For now, let's just add it. The user wants "all" links.
                     # But we must be careful not to crawl the whole site.
                     # We can check if the link text contains "480p" or "720p" or "1080p"
                     nav_text_lower = n['text'].lower()
                     if any(q in nav_text_lower for q in ['480p', '720p', '1080p', 'hevc']):
                         queue.append(n['link'])

        processed_count += 1

    # Step 3: Print Results
    print("\n" + "="*50)
    print("FINAL RESULTS")
    print("="*50)

    if not results:
        print("No results found.")

    # Sort keys to hopefully put them in order
    for title in sorted(results.keys()):
        print(f"\n--- {title} ---")
        if not results[title]:
            print("  No download links found.")
        for link in results[title]:
            print(f"  {link['text']}: {link['link']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        start_url = sys.argv[1]
    else:
        start_url = input("Enter gadgetsweb.xyz link: ")

    main(start_url)
