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

start_urls = ['https://www.merckvetmanual.com/resourcespages/pet-owners-overview', 
              'https://www.merckvetmanual.com/veterinary-topics']

paths_to_skip = ['/resource', '/authors', '/reference-values-and-conversion-tables/reference-guides', 
                 '/pages-with-widgets/quizzes','/resourcespages/about', '/resourcespages/glossary']

sleep_time = 5000 # 5 seconds
consecutive_requests = 100

async def find_urls(page, base_url="https://www.merckvetmanual.com/"):
    """
    Finds all internal article links on the page and returns a list of unique absolute URLs.
    Filters out external links and removes fragment identifiers.
    """
    links = await page.query_selector_all("#mainContainer a")
    seen = set()
    unique_hrefs = []

    for link in links:
        href = await link.get_attribute("href")
        """ TODO:
            - Add list of paths to skip, i.e authors, ...
            - different storing, aka in folder with path of the initially given url
            - visited should be stored as well at the same time as the content pages. 
              That way, we can skip the visited pages in the next scraping session.
            - Check if request.text contains urls to know if bs4 is an option
            - possible to update visited.txt dynamically?
        """

        if not href or (not href.startswith("/")) or (href in paths_to_skip):
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
            print("✅ base href:", clean_url)

    return unique_hrefs


async def crawl(start_urls, page, base_url):
    final_content_urls = []

    with open('./visited.txt', "r", encoding="utf-8") as f:
        visited = set(line.strip() for line in f if line.strip())
    with open('./to_explore.txt', "r", encoding="utf-8") as f:
        if os.path.getsize('./to_explore.txt') == 0:
            to_explore = list(start_urls)
        else: 
            to_explore = list(line.strip() for line in f if line.strip())
    print(len(to_explore), len(visited))
    request_count = 0

    while to_explore:
        print(f"Number of URLs to explore: {len(to_explore)}")
        current_url = to_explore.pop()
        if current_url in visited:
            continue
        visited.add(current_url)

        print(f"\nVisiting: {current_url}")
        try:
            response = await page.goto(current_url, wait_until="domcontentloaded")
            if response.status == 403: 
                print(f"HTTP error 403, requests are being blocked, terminating script for now.")
                with open("./visited.txt", "a", encoding="utf-8") as f:
                    for url in visited:
                        f.write(url + "\n")
                with open("./to_explore.txt", "w", encoding="utf-8") as f:
                    for url in to_explore:
                        f.write(url + "\n")
                return final_content_urls
            request_count += 1
            if (request_count % consecutive_requests) == 0:
                print(f"✅ Requests made: {request_count}, sleeping for {sleep_time} ms")
                await asyncio.sleep(sleep_time / 1000)  # Convert to seconds
        except Exception as e:
            print(f"❌ Failed to load {current_url}: {e}")
            continue

        main_content = await page.query_selector('[data-testid="topic-main-content"]')
        if main_content:
            print(f"✅ Content found at: {current_url}")
            final_content_urls.append(current_url)
            continue

        print(f"🔍 No main content found, searching for more links on {current_url}...")
        found_urls = await find_urls(page)

        # Normalize new URLs before adding
        normalized = [urljoin(base_url, url) for url in found_urls if urljoin(base_url, url) not in visited]
        to_explore.extend(normalized)

    return final_content_urls

async def main():
    #start_urls = sys.argv[1:]

    #if not start_urls:
    #    print("Usage: python crawler.py <url1> <url2> ...")
    #    sys.exit(1)

    playwright, browser, page = await init_browser(headless=True)
    base_url = "https://www.merckvetmanual.com/"
    content_urls = await crawl(start_urls, page, base_url)

    # Save to file
    with open("./content_urls.txt", "a", encoding="utf-8") as f:
        for url in content_urls:
            f.write(url + "\n")

    print(f"✅ Saved {len(content_urls)} URLs to content_urls.txt")
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())