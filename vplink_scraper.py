import requests
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

def bypass_vplink(url):
    """
    Bypasses vplink.in protection to get the destination link.
    Note: This site detects VPNs/Proxies. This script must be run from a clean IP.
    It attempts to follow the chain of "Next", "Continue", or "Get Link" buttons.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://vplink.in/",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    session = requests.Session()
    session.headers.update(headers)

    current_url = url
    # Limit redirects to avoid infinite loops
    max_steps = 10
    step = 0

    while step < max_steps:
        step += 1
        print(f"Step {step}: Accessing {current_url}...")

        try:
            response = session.get(current_url, allow_redirects=True)
        except Exception as e:
            print(f"Error accessing {current_url}: {e}")
            return None

        # Check if VPN detected
        if "VPN Detected" in response.text:
            print("Error: VPN Detected by vplink.in. This script must be run from a non-VPN/Proxy IP.")
            return None

        # Check if we have reached a final destination (heuristic)
        # If the domain has changed significantly from vplink/related shorteners and is a target domain
        domain = urlparse(response.url).netloc
        if "vplink.in" not in domain and "shrinke" not in domain and "short" not in domain:
            # Check if it looks like a final destination (e.g. hubcloud, gofile, drive)
            if any(x in domain for x in ['hubcloud', 'hubdrive', 'hubcdn', 'gofile.io', 'drive.google', 'mega.nz', 'pixeldrain', '1fichier']):
                 print(f"Reached final destination: {response.url}")
                 return response.url

            # Or if the user just wants the "original link", and we are out of the vplink loop
            # But sometimes we might land on an intermediate ad page.
            # Let's verify if there is a "Get Link" button on this page too.

        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Check for Meta Refresh
        meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'refresh', re.I)})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            match = re.search(r'url=([^;]+)', content, re.I)
            if match:
                next_url = match.group(1).strip()
                print(f"Found Meta Refresh to: {next_url}")
                current_url = urljoin(response.url, next_url)
                time.sleep(1) # Be polite and wait a bit
                continue

        # 2. Check for JavaScript redirect
        scripts = soup.find_all('script')
        found_js_redirect = False
        for script in scripts:
            if script.string:
                # Pattern: window.location.href = "..." or window.location = "..."
                match = re.search(r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']', script.string)
                if match:
                    next_url = match.group(1)
                    print(f"Found JS Redirect to: {next_url}")
                    current_url = urljoin(response.url, next_url)
                    found_js_redirect = True
                    break

                # Pattern: location.replace("...")
                match = re.search(r'location\.replace\(["\']([^"\']+)["\']\)', script.string)
                if match:
                    next_url = match.group(1)
                    print(f"Found JS Redirect (replace) to: {next_url}")
                    current_url = urljoin(response.url, next_url)
                    found_js_redirect = True
                    break

        if found_js_redirect:
            time.sleep(1)
            continue

        # 3. Look for "Next", "Continue", "Get Link" buttons/forms
        # Common patterns: <a id="getlink">, <button id="submit">, forms

        # Form submission?
        form = soup.find('form', id='landing') # Example pattern
        if form:
             # Try to submit this form
             action = form.get('action')
             method = form.get('method', 'get').lower()
             if action:
                 next_url = urljoin(response.url, action)
                 inputs = form.find_all('input')
                 data = {}
                 for inp in inputs:
                     name = inp.get('name')
                     value = inp.get('value', '')
                     if name:
                         data[name] = value

                 print(f"Submitting form to {next_url}")
                 if method == 'post':
                     try:
                        # Perform POST request
                        resp = session.post(next_url, data=data, allow_redirects=True)

                        # If we got redirected, update current_url and let the loop handle the new page
                        if resp.history or resp.url != next_url:
                             current_url = resp.url
                             # Wait a bit before next step
                             time.sleep(1)
                             continue

                        # If no redirect, maybe the response contains the next link?
                        # We can't easily inject this response back into the loop's start (which does GET).
                        # For now, let's assume the POST should have redirected.
                        print("Form submitted but no redirect detected.")
                     except Exception as e:
                        print(f"Form submission failed: {e}")
                 else:
                     # GET form
                     try:
                         # For GET, we can just construct the URL with params and let the loop fetch it
                         req = requests.Request('GET', next_url, params=data)
                         prepped = session.prepare_request(req)
                         current_url = prepped.url
                         print(f"Form GET URL: {current_url}")
                         time.sleep(1)
                         continue
                     except Exception as e:
                         print(f"Form preparation failed: {e}")

        # Look for "Get Link" button
        get_link_btn = soup.find('a', string=re.compile(r"Get Link|Continue|Next|Go to Link", re.I))
        if get_link_btn and get_link_btn.get('href'):
             next_url = get_link_btn['href']
             if not next_url.startswith('javascript'):
                 print(f"Found Link button: {next_url}")
                 current_url = urljoin(response.url, next_url)
                 time.sleep(1)
                 continue

        # Look for element with id="landing" or similar that might be a link
        landing_link = soup.find('a', id='landing')
        if landing_link and landing_link.get('href'):
             next_url = landing_link['href']
             print(f"Found landing link: {next_url}")
             current_url = urljoin(response.url, next_url)
             time.sleep(1)
             continue

        # If we are here, we ran out of obvious moves.
        # Let's check for the heuristic "potential link" from before as a fallback
        ignored_domains = [
            'facebook.com', 'twitter.com', 'instagram.com', 'telegram.me', 't.me',
            'whatsapp.com', 'google.com', 'youtube.com', 'pinterest.com', 'linkedin.com',
            'vplink.in', 'cloudflare.com'
        ]

        potential_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            parsed = urlparse(href)
            if not parsed.netloc:
                 continue

            # If it's a known file host, prioritize it immediately
            if any(x in parsed.netloc for x in ['hubcloud', 'hubdrive', 'hubcdn', 'gofile.io', 'drive.google', 'mega.nz']):
                return href

            is_ignored = False
            for dom in ignored_domains:
                if dom in parsed.netloc:
                    is_ignored = True
                    break
            if is_ignored:
                continue

            potential_links.append(href)

        if potential_links:
            # If we found links but none matched the "known hosts", maybe return the first one?
            # But be careful not to return ads.
            print(f"Found potential link (fallback): {potential_links[0]}")
            # If we are deep in steps (e.g. step > 1), it's more likely to be the result
            if step > 1:
                return potential_links[0]

            # If it's step 1 and we found a link, maybe we should follow it?
            current_url = potential_links[0]
            continue

        print("No further steps found.")
        break

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
