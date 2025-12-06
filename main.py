import requests
from bs4 import BeautifulSoup
import sys

def search_movies(query):
    print(f"Searching for '{query}'...")
    search_url = "https://search.pingora.fyi/collections/post/documents/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://hdhub4u.rehab/"
    }

    params = {
        "q": query,
        "query_by": "post_title",
        "sort_by": "sort_by_date:desc",
        "limit": "15",
        "highlight_fields": "none",
        "use_cache": "true",
        "page": "1"
    }

    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('hits', [])
    except requests.exceptions.RequestException as e:
        print(f"Error searching: {e}")
        return []

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

    soup = BeautifulSoup(response.content, 'lxml')

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
        user_input = input("Enter Hdhub4u movie link or search query: ")

    # Check if input is a URL
    if user_input.startswith("http://") or user_input.startswith("https://"):
        url = user_input
    else:
        # It's a search query
        hits = search_movies(user_input)
        if not hits:
            print("No results found.")
            sys.exit(0)

        print(f"\nFound {len(hits)} results:")
        for idx, hit in enumerate(hits):
            doc = hit['document']
            print(f"{idx + 1}. {doc['post_title']}")

        try:
            choice = int(input("\nSelect a movie (enter number): ")) - 1
            if 0 <= choice < len(hits):
                selected_hit = hits[choice]
                permalink = selected_hit['document']['permalink']
                url = f"https://hdhub4u.rehab{permalink}"
            else:
                print("Invalid selection.")
                sys.exit(1)
        except ValueError:
            print("Invalid input.")
            sys.exit(1)

    links = scrape_hdhub4u(url)
    if links:
        print(f"Found {len(links)} links:")
        for link in links:
            print(f"{link['text']}: {link['link']}")
