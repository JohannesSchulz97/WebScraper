import asyncio
from playwright.async_api import async_playwright
import sys, os
from urllib.parse import urlparse, urlunparse, urljoin

async def init_browser(headless=True):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context(viewport={"width": 1200, "height": 800})
    page = await context.new_page()
    return playwright, browser, page


from urllib.parse import urlparse, urlunparse, urljoin

base_url = "https://www.merckvetmanual.com/"

start_urls = ['https://www.merckvetmanual.com/resourcespages/pet-owners-overview', 
              'https://www.merckvetmanual.com/veterinary-topics']

paths_to_skip = ['/resource', '/authors', '/reference-values-and-conversion-tables/reference-guides', 
                 '/pages-with-widgets/quizzes','/resourcespages/about', '/resourcespages/glossary']

sleep_time = 10000 
consecutive_requests = 100

class AccessDenied(Exception):
    def __init__(self, url):
        super().__init__(f"403 Forbidden: Access denied to {url}")
        self.url = url

async def find_urls(page):
    """
    Finds all internal article links on the page and returns a list of unique relative URLs.
    Filters out external links and removes fragment identifiers.
    """
    links = await page.query_selector_all("#mainContainer a")
    seen = set()
    unique_hrefs = []

    for link in links:
        href = await link.get_attribute("href")
        if (not href or (not href.startswith("/")) 
                        or any(href.startswith(skip_path) for skip_path in paths_to_skip)):
            print(f"❌ Skipping link: {href}")
            continue  # Skip empty, external and irrelevant links

        # Convert to absolute URL
        full_url = urljoin(base_url, href)

        # Remove fragment identifiers (e.g., #section)
        parsed = urlparse(full_url)
        clean_url = urlunparse(parsed._replace(fragment=""))

        # Deduplicate while preserving order
        if clean_url not in seen:
            seen.add(clean_url)
            unique_hrefs.append(clean_url)
            print("✅ Added to to_explore:", clean_url)

    return unique_hrefs



async def crawl(page):

    # Retrieve visited and to_explore URLs from files
    with open('./data/visited.txt', "r", encoding="utf-8") as f:
        visited = set(line.strip() for line in f if line.strip())
    with open('./data/to_explore.txt', "r", encoding="utf-8") as f:
        if os.path.getsize('./data/to_explore.txt') == 0:
            to_explore = set(start_urls)
        else: 
            to_explore = set(line.strip() for line in f if line.strip())
    print(f"Urls to explore: {len(to_explore)}")
    print(f"Urls already visited: {len(visited)}")
    with open('./data/content_urls.txt', 'r', encoding='utf-8') as f:
        num_lines = sum(1 for _ in f)
    print(f"Number of Content Urls: {num_lines}")
    content_urls = []
    request_count = 0
    try: 
        while to_explore:
            print(f"Number of URLs to explore: {len(to_explore)}")
            current_url = to_explore.pop()
            if current_url in visited:
                continue

            print(f"\nVisiting: {current_url}")
            try:
                response = await page.goto(current_url, wait_until="domcontentloaded")
            except Exception as e:
                print(f"❌ Failed to load {current_url}: {e}")
                continue
            if response.status == 403: 
                print(f"HTTP error 403, requests are being blocked, terminating script for now.")
                to_explore.add(current_url)
                raise AccessDenied(current_url)
            
            visited.add(current_url)
            request_count += 1
            if (request_count % consecutive_requests) == 0:
                print(f"✅ Requests made: {request_count}, sleeping for {sleep_time} ms")
                await asyncio.sleep(sleep_time / 1000)  # Convert to seconds

            main_content = await page.query_selector('[data-testid="topic-main-content"]')
            if main_content:
                print(f"✅ Content found at: {current_url}")
                content_urls.append(current_url)
                continue

            print(f"🔍 No main content found, searching for more links on {current_url}...")
            found_urls = await find_urls(page)
            # add new URLS only if they are not in visited
            unexplored = [url for url in found_urls if url not in visited]
            to_explore.update(unexplored)
    finally:
        # Always save progress whether stopped normally, due to an exception or with Ctrl+C
        with open("./data/visited.txt", "w", encoding="utf-8") as f:
            for url in visited:
                f.write(url + "\n")
        with open("./data/to_explore.txt", "w", encoding="utf-8") as f:
            for url in to_explore:
                f.write(url + "\n")
        with open("./data/content_urls.txt", "a", encoding="utf-8") as f:
            for url in content_urls:
                f.write(url + "\n")
        print(f"💾 Progress saved: \n")
        print(f"Urls to explore: {len(to_explore)}")
        print(f"Urls already visited: {len(visited)}")
        print(f"Number of Content Urls: {len(content_urls)}")

async def main():

    playwright, browser, page = await init_browser(headless=True)

    await crawl(page)

    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())