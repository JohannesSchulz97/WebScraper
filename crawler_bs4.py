import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, urljoin
import sys

def find_urls(page_content, base_url="https://www.merckvetmanual.com/"):
    """
    Finds all internal article links in the page content and returns a list of unique absolute URLs.
    Filters out external links and removes fragment identifiers.
    """
    soup = BeautifulSoup(page_content, "html.parser")
    links = soup.select("#mainContainer a")
    seen = set()
    unique_hrefs = []

    for link in links:
        href = link.get("href")
        if not href or not href.startswith("/"):
            continue  # Skip empty or external links

        # Convert to absolute URL
        full_url = urljoin(base_url, href)

        # Remove fragment identifiers (e.g., #section)
        parsed = urlparse(full_url)
        clean_url = urlunparse(parsed._replace(fragment=""))

        # Deduplicate while preserving order
        if clean_url not in seen:
            seen.add(clean_url)
            unique_hrefs.append(clean_url)
            print("✅ base href:", clean_url)

    return unique_hrefs

def crawl(start_urls, base_url="https://www.merckvetmanual.com/"):
    to_explore = list(start_urls)
    final_content_urls = []
    visited = set()

    while to_explore:
        current_url = to_explore.pop()
        if current_url in visited:
            continue
        visited.add(current_url)

        print(f"\nVisiting: {current_url}")
        try:
            response = requests.get(current_url)
            response.raise_for_status()  # Will raise an exception for 4xx/5xx
        except Exception as e:
            print(f"❌ Failed to load {current_url}: {e}")
            continue
        with open("static-html.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        print()
        # Check for content (e.g., specific element or a condition to identify relevant pages)
        if "topic-main-content" in response.text:
            print(f"✅ Content found at: {current_url}")
            final_content_urls.append(current_url)
            continue

        print(f"🔍 No main content found, searching for more links on {current_url}...")
        found_urls = find_urls(response.text, base_url)

        # Normalize new URLs before adding
        normalized = [urljoin(base_url, url) for url in found_urls if urljoin(base_url, url) not in visited]
        to_explore.extend(normalized)

    return final_content_urls

def main():
    start_urls = sys.argv[1:]

    if not start_urls:
        print("Usage: python crawler.py <url1> <url2> ...")
        sys.exit(1)

    base_url = "https://www.merckvetmanual.com/"
    content_urls = crawl(start_urls, base_url)

    # Save to file
    with open("content_urls_bs4.txt", "w", encoding="utf-8") as f:
        for url in content_urls:
            f.write(url + "\n")

    print(f"✅ Saved {len(content_urls)} URLs to content_urls.txt")

if __name__ == "__main__":
    main()