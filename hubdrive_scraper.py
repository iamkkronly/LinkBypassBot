import requests
from bs4 import BeautifulSoup
import sys
import json
import re

# Helper function to check if a URL is a Hubdrive link
def is_hubdrive_url(url):
    return "hubdrive.space" in url or "hubdrive.me" in url # Add other domains if known

def scrape_hdhub4u(url):
    print(f"Scraping movie page: {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []

    soup = BeautifulSoup(response.content, 'lxml')

    links = []

    # We look for all 'a' tags
    for a_tag in soup.find_all('a', href=True):
        text = a_tag.get_text().strip()
        href = a_tag['href']

        # Filter for quality indicators and ensure it's a Hubdrive link
        # Note: The original main.py filtered for quality in text, but we also want to ensure it's a link we can process.
        # But maybe the links on Hdhub4u ARE Hubdrive links (or redirect to them).
        if any(q in text.lower() for q in ['480p', '720p', '1080p', 'episode']):
            # We store the link and the text (quality)
            links.append({'quality': text, 'link': href})

    if not links:
        print("No download links found on the movie page.")
        return []

    return links

def bypass_hubdrive(url):
    print(f"Bypassing Hubdrive: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": url,
        "Origin": "https://hubdrive.space"
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        # Step 1: Get the main page to find the ID
        response = session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Extract the ID
        down_id_div = soup.find('div', id='down-id')
        if not down_id_div:
            # It might be a different structure or not a Hubdrive file page
            print("Could not find 'down-id' element. Is this a valid Hubdrive file page?")
            return None

        file_id = down_id_div.get_text().strip()
        # print(f"Found File ID: {file_id}")

        # Step 2: Make the AJAX request
        ajax_url = "https://hubdrive.space/ajax.php?ajax=direct-download"
        data = {'id': file_id}

        # Ensure Content-Type is set for POST
        session.headers.update({"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})

        # print(f"Sending POST request to {ajax_url}...")
        response = session.post(ajax_url, data=data)
        response.raise_for_status()

        try:
            json_response = response.json()
        except json.JSONDecodeError:
            print("Failed to decode JSON response.")
            return None

        if json_response.get('code') == "200":
            download_data = json_response.get('data')

            # The 'data' field can be a JSON object containing the link
            if isinstance(download_data, dict):
                gd_link = download_data.get('gd')
                if gd_link:
                    return gd_link

            # Fallback/alternative handling if structure varies
            print("Direct download link not found in response data.")
            print(json_response)
            return None

        else:
            print(f"Hubdrive Error: {json_response.get('code')} - {json_response.get('file')}")
            return None

    except Exception as e:
        print(f"An error occurred while bypassing {url}: {e}")
        return None

def process_url(url):
    if is_hubdrive_url(url):
        # Single Hubdrive link
        direct_link = bypass_hubdrive(url)
        if direct_link:
            print(f"Direct Download Link: {direct_link}")
        else:
            print("Failed to retrieve direct link.")
    else:
        # Assume it's a movie page (e.g. Hdhub4u)
        links = scrape_hdhub4u(url)
        if links:
            print(f"Found {len(links)} links. Processing...")
            for item in links:
                print(f"\nProcessing {item['quality']}...")
                # The link might be a Hubdrive link or something else.
                # If it's Hdhub4u, the links usually point to Hubdrive or similar.
                # We should check if the link itself is a Hubdrive link.
                if is_hubdrive_url(item['link']):
                    direct_link = bypass_hubdrive(item['link'])
                    if direct_link:
                        print(f"  Direct Link: {direct_link}")
                    else:
                        print("  Failed to bypass.")
                else:
                    print(f"  Skipping non-Hubdrive link: {item['link']}")
        else:
             print("No links found or not a supported URL.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        default_link = "https://hdhub4u.rehab/bigg-boss-season-19-hindi-webrip-all-episodes/"
        url = input(f"Enter Hubdrive link or Movie Page URL (default: {default_link}): ") or default_link

    process_url(url)
