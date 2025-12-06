import requests
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

def bypass_vplink(url):
    """
    Bypasses vplink.in protection to get the destination link.
    Note: This site detects VPNs/Proxies. This script must be run from a clean IP.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://vplink.in/",
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        print(f"Accessing {url}...")
        response = session.get(url, allow_redirects=True)

        # Check if VPN detected
        if "VPN Detected" in response.text:
            print("Error: VPN Detected by vplink.in. This script must be run from a non-VPN/Proxy IP.")
            return None

        # Check for immediate redirect (Meta Refresh)
        # Use html.parser for better portability, though lxml is in requirements.txt
        soup = BeautifulSoup(response.content, 'html.parser')

        meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'refresh', re.I)})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            match = re.search(r'url=([^;]+)', content, re.I)
            if match:
                redirect_url = match.group(1).strip()
                print(f"Found Meta Refresh to: {redirect_url}")
                return redirect_url

        # Check for JavaScript redirect (window.location)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Pattern: window.location.href = "..." or window.location = "..."
                match = re.search(r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']', script.string)
                if match:
                    redirect_url = match.group(1)
                    print(f"Found JS Redirect to: {redirect_url}")
                    return redirect_url

                # Pattern: location.replace("...")
                match = re.search(r'location\.replace\(["\']([^"\']+)["\']\)', script.string)
                if match:
                    redirect_url = match.group(1)
                    print(f"Found JS Redirect (replace) to: {redirect_url}")
                    return redirect_url

        # Heuristic: Find potential external link
        # Filter out common junk
        ignored_domains = [
            'facebook.com', 'twitter.com', 'instagram.com', 'telegram.me', 't.me',
            'whatsapp.com', 'google.com', 'youtube.com', 'pinterest.com', 'linkedin.com',
            'vplink.in', 'cloudflare.com'
        ]

        potential_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Basic filters
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue

            # Domain check
            parsed = urlparse(href)
            if not parsed.netloc: # Relative link
                 continue

            is_ignored = False
            for domain in ignored_domains:
                if domain in parsed.netloc:
                    is_ignored = True
                    break

            if is_ignored:
                continue

            # If we are here, it's a potential link
            print(f"Found potential link: {href}")
            potential_links.append(href)

        if potential_links:
            # If multiple links, maybe prefer the one that looks like a file host or contains specific keywords?
            # For now, return the first one as a best guess.
            return potential_links[0]

        print("Could not find destination link.")
        return None

    except Exception as e:
        print(f"Error bypassing vplink: {e}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = bypass_vplink(url)
        if result:
            print(f"Destination: {result}")
    else:
        print("Usage: python vplink_scraper.py <url>")
