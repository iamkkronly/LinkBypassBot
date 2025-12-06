import requests
from bs4 import BeautifulSoup
import re
import sys
import json
import base64
from urllib.parse import urlparse, urljoin, parse_qs

class UniversalScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get_soup(self, content):
        try:
            return BeautifulSoup(content, 'lxml')
        except Exception as e:
            print(f"lxml parsing failed ({e}). Falling back to html.parser.")
            return BeautifulSoup(content, 'html.parser')

    def scrape(self, url):
        """
        Main entry point. Detects URL type and delegates.
        """
        print(f"Processing: {url}")
        domain = urlparse(url).netloc

        if "hubcloud" in domain:
            return self.handle_hubcloud(url)
        elif "hubdrive" in domain:
            return self.handle_hubdrive(url)
        elif "hubcdn" in domain:
            return self.handle_hubcdn(url)
        elif "gofile.io" in domain:
            return self.handle_gofile(url)
        elif "vplink.in" in domain:
            return self.handle_vplink(url)
        else:
            print(f"Unknown domain: {domain}. Trying generic scrape or Hdhub4u logic.")
            return self.handle_generic_movie_page(url)

    def handle_hubcloud(self, url):
        print("Detected HubCloud URL.")
        links = []
        try:
            # Step 1: Fetch the initial HubCloud page
            response = self.session.get(url, allow_redirects=True)
            response.raise_for_status()
            soup = self._get_soup(response.content)

            # Step 2: Find the "Generate Direct Download Link" or similar intermediate link
            # It usually points to gamerxyt.com or similar
            next_url = None

            # Method A: Look for specific text
            generate_btn = soup.find('a', string=re.compile(r"Generate Direct Download Link", re.I))
            if generate_btn and generate_btn.get('href'):
                next_url = generate_btn['href']

            # Method B: Look for known intermediate domains if Method A fails
            if not next_url:
                for a in soup.find_all('a', href=True):
                    if "gamerxyt.com" in a['href']:
                        next_url = a['href']
                        break

            if next_url:
                print(f"Found intermediate link: {next_url}")
                # Step 3: Fetch the intermediate link (this will redirect to the final page, e.g., carnewz.site)
                response = self.session.get(next_url, allow_redirects=True)
                response.raise_for_status()
                soup = self._get_soup(response.content)
            else:
                print("No intermediate link found. Checking current page for links.")
                # If no intermediate link, maybe we are already on the page?
                pass

            # Step 4: Scrape the final page for download links
            # We look for pixeldrain, etc.

            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text().strip()

                # Filter out navigation/ads
                if any(x in href for x in ['pixeldrain', 'drive.google.com', 'mega.nz', '1fichier', 'gofile.io']):
                    links.append({'text': text, 'link': href})
                elif any(q in text.lower() for q in ['480p', '720p', '1080p', 'mkv', 'zip']):
                    if href.startswith('http'):
                        links.append({'text': text, 'link': href})
                elif "download [" in text.lower() and "]" in text:
                    if href.startswith('http'):
                        links.append({'text': text, 'link': href})

            return links

        except Exception as e:
            print(f"Error scraping HubCloud: {e}")
            return []

    def handle_hubdrive(self, url):
        print("Detected HubDrive URL.")
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = self._get_soup(response.content)

            # Look for "HubCloud Server" link
            hubcloud_link = None
            for a in soup.find_all('a', href=True):
                if "HubCloud Server" in a.get_text() or "hubcloud" in a['href']:
                    # Double check if it looks like a drive/pack link
                    if "drive" in a['href']:
                        hubcloud_link = a['href']
                        break

            if hubcloud_link:
                print(f"Found HubCloud Server link: {hubcloud_link}")
                return self.handle_hubcloud(hubcloud_link)
            else:
                print("No HubCloud Server link found. Attempting single file bypass.")
                # Use existing HubDrive bypass logic
                down_id = soup.find('div', id='down-id')
                if down_id:
                    file_id = down_id.get_text().strip()
                    ajax_url = "https://hubdrive.space/ajax.php?ajax=direct-download"
                    data = {'id': file_id}
                    post_resp = self.session.post(ajax_url, data=data, headers={"X-Requested-With": "XMLHttpRequest"})
                    if post_resp.status_code == 200:
                        try:
                            json_resp = post_resp.json()
                            if json_resp.get('code') == "200" and 'data' in json_resp:
                                if isinstance(json_resp['data'], dict) and 'gd' in json_resp['data']:
                                    return [{'text': 'Direct Download', 'link': json_resp['data']['gd']}]
                        except:
                            pass

                return []

        except Exception as e:
            print(f"Error handling HubDrive: {e}")
            return []

    def handle_hubcdn(self, url):
        print("Detected HubCDN URL.")
        try:
            # Logic from hubcdn_bypasser.py
            response = self.session.get(url, allow_redirects=True)
            response.raise_for_status()

            match = re.search(r'var\s+reurl\s*=\s*["\']([^"\']+)["\']', response.text)
            if not match:
                if 'hubcdn.fans/dl/' in response.url:
                     final_url = response.url
                else:
                     print(f"Could not find redirect URL in {url}")
                     return []
            else:
                redirect_url = match.group(1)
                parsed_url = urlparse(redirect_url)
                query_params = parse_qs(parsed_url.query)
                if 'r' not in query_params:
                    print(f"Could not find 'r' parameter in {redirect_url}")
                    return []
                r_param = query_params['r'][0]
                try:
                    decoded_url = base64.b64decode(r_param).decode('utf-8')
                    final_url = decoded_url
                except Exception as e:
                    print(f"Error decoding base64: {e}")
                    return []

            response = self.session.get(final_url)
            response.raise_for_status()
            soup = self._get_soup(response.content)
            a_tag = soup.find('a', id='vd')

            if a_tag and a_tag.get('href'):
                return [{'text': 'Direct Download', 'link': a_tag['href']}]
            else:
                print("Could not find direct download link (id='vd') on the page.")
                return []

        except Exception as e:
            print(f"Error handling HubCDN: {e}")
            return []

    def handle_gofile(self, url):
        print("Detected GoFile URL.")
        try:
            content_id = url.split('/')[-1]

            # 1. Create Account (Guest) to get token
            account_resp = requests.post("https://api.gofile.io/accounts", headers=self.headers)
            if account_resp.status_code == 200:
                account_data = account_resp.json()
                if account_data['status'] == 'ok':
                    token = account_data['data']['token']
                    print(f"Got Gofile Token: {token}")

                    # 2. Get Content
                    content_url = f"https://api.gofile.io/contents/{content_id}?wt={token}"
                    content_resp = requests.get(content_url, headers={"Authorization": f"Bearer {token}"})

                    if content_resp.status_code == 200:
                        content_data = content_resp.json()
                        if content_data['status'] == 'ok':
                            items = content_data['data']['children']
                            links = []
                            for item_id, item in items.items():
                                link = item.get('link')
                                name = item.get('name')
                                if link:
                                    links.append({'text': name, 'link': link})
                            return links

            return [{'text': 'GoFile Link (Manual Visit Required)', 'link': url}]

        except Exception as e:
            print(f"Error handling GoFile: {e}")
            return [{'text': 'GoFile Link', 'link': url}]

    def handle_vplink(self, url):
        print("Detected vplink.in URL.")
        try:
            # Import here to avoid top-level issues if file is missing
            try:
                from vplink_scraper import bypass_vplink
            except ImportError:
                print("vplink_scraper module not found.")
                return []

            result = bypass_vplink(url)
            if result:
                # The result might be another scrapable URL
                print(f"Resolved vplink to: {result}")

                # Check if it's a known domain and recurse
                domain = urlparse(result).netloc
                if "hubcloud" in domain or "hubdrive" in domain or "hubcdn" in domain or "gofile.io" in domain:
                    return self.scrape(result)
                else:
                    return [{'text': 'Direct Link', 'link': result}]
            else:
                return []

        except Exception as e:
            print(f"Error handling vplink: {e}")
            return []

    def handle_generic_movie_page(self, url):
        print("Attempting to scrape as movie page.")
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = self._get_soup(response.content)

            links = []
            for a_tag in soup.find_all('a', href=True):
                text = a_tag.get_text().strip()
                href = a_tag['href']

                if any(q in text.lower() for q in ['480p', '720p', '1080p', 'episode']):
                    links.append({'text': text, 'link': href})

            return links
        except Exception as e:
            print(f"Error scraping generic page: {e}")
            return []

if __name__ == "__main__":
    scraper = UniversalScraper()

    if len(sys.argv) > 1:
        # Check if comma separated
        urls = sys.argv[1].split(',')
        for url in urls:
            url = url.strip()
            if not url: continue

            print(f"\n--- Processing {url} ---")
            results = scraper.scrape(url)
            if results:
                print("Found Links:")
                for r in results:
                    print(f"{r['text']}: {r['link']}")
            else:
                print("No links found.")
    else:
        print("Please provide URLs as argument.")
