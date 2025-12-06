import requests
import re
import base64
import sys
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

def get_soup(content):
    try:
        return BeautifulSoup(content, 'lxml')
    except Exception as e:
        print(f"lxml parsing failed ({e}). Falling back to html.parser.")
        return BeautifulSoup(content, 'html.parser')

# Import the scraper from hdhub4u_scraper.py
try:
    from hdhub4u_scraper import scrape_hdhub4u
except ImportError:
    # Fallback if hdhub4u_scraper.py is not in the same directory or path issues
    def scrape_hdhub4u(url):
        print("Scraper module not found.")
        return []

def bypass_hubcdn_link(url):
    """
    Bypasses the Hubcdn protection to get the direct download link.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Step 1: Fetch the initial Hubcdn page
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(url, allow_redirects=True)
        response.raise_for_status()

        # Step 2: Extract the 'reurl' variable
        # Content looks like: var reurl = "https://inventoryidea.com/?r=...";
        match = re.search(r'var\s+reurl\s*=\s*["\']([^"\']+)["\']', response.text)
        if not match:
            # Maybe it's already the final page?
            if 'hubcdn.fans/dl/' in response.url:
                 final_url = response.url
            else:
                 print(f"Could not find redirect URL in {url}")
                 return None
        else:
            redirect_url = match.group(1)

            # Step 3: Extract the 'r' parameter from the redirect URL
            parsed_url = urlparse(redirect_url)
            query_params = parse_qs(parsed_url.query)
            if 'r' not in query_params:
                print(f"Could not find 'r' parameter in {redirect_url}")
                return None

            r_param = query_params['r'][0]

            # Step 4: Base64 decode the 'r' parameter
            try:
                decoded_url = base64.b64decode(r_param).decode('utf-8')
            except Exception as e:
                print(f"Error decoding base64: {e}")
                return None

            # Step 5: Fetch the decoded URL (the /dl/ page)
            final_url = decoded_url

        # print(f"Accessing final page: {final_url}")
        response = session.get(final_url)
        response.raise_for_status()

        # Step 6: Extract the direct download link from <a id="vd">
        soup = get_soup(response.content)
        a_tag = soup.find('a', id='vd')

        if a_tag and a_tag.get('href'):
            return a_tag['href']
        else:
            print("Could not find direct download link (id='vd') on the page.")
            return None

    except Exception as e:
        print(f"Error bypassing {url}: {e}")
        return None

def process_url(url):
    """
    Processes the input URL.
    If it's a Hubcdn link, bypasses it.
    If it's a movie page (Hdhub4u), scrapes all links and bypasses them.
    """
    if "hubcdn.fans" in url:
        print(f"Processing single Hubcdn link: {url}")
        direct_link = bypass_hubcdn_link(url)
        if direct_link:
            print(f"Direct Link: {direct_link}")
        else:
            print("Failed to retrieve direct link.")
    else:
        # Assume it's a movie page (e.g., Hdhub4u)
        print(f"Processing movie page: {url}")
        links = scrape_hdhub4u(url)

        if not links:
            print("No Hubcdn links found on the page.")
            return

        print(f"Found {len(links)} links. Bypassing them now...")
        for item in links:
            print(f"\nQuality: {item['text']}")
            hub_url = item['link']
            # Sometimes links might be relative or wrapped, but scrape_hdhub4u usually returns hrefs.
            # Assuming they are Hubcdn links.
            if "hubcdn.fans" in hub_url:
                direct_link = bypass_hubcdn_link(hub_url)
                if direct_link:
                    print(f"Direct Link: {direct_link}")
                else:
                    print(f"Failed to bypass: {hub_url}")
            else:
                print(f"Skipping non-Hubcdn link: {hub_url}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_url = sys.argv[1]
    else:
        input_url = input("Enter Hubcdn link or Movie Page URL: ")

    process_url(input_url)
