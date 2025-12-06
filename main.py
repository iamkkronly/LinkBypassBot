import requests
from bs4 import BeautifulSoup
import sys
from hdhub4u_scraper import scrape_hdhub4u
from hubcdn_bypasser import process_url

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


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        user_input = input("Enter Hdhub4u movie link or search query: ")

    # Check if input is a URL
    if user_input.startswith("http://") or user_input.startswith("https://"):
        if "hubcdn.fans" in user_input:
            process_url(user_input)
            sys.exit(0)
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
