import asyncio
import json
from playwright.async_api import async_playwright
import argparse
import os
import datetime
from tqdm import tqdm

class AccessDenied(Exception):
    def __init__(self, url):
        super().__init__(f"403 Forbidden: Access denied to {url}")
        self.url = url

sleep_time = 180 
import sys
import os
from datetime import datetime

class DualLogger:
    def __init__(self, log_path):
        self.terminal = sys.stdout
        self.log = open(log_path, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # This is needed for compatibility with Python's logging system
        self.terminal.flush()
        self.log.flush()

# Create logs folder if not exist
os.makedirs("logs", exist_ok=True)

# Generate timestamped filename
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = f"logs/scraper_log_{timestamp}.txt"

sys.stdout = DualLogger(log_file)
sys.stderr = sys.stdout  # This sends error messages to the same log
"""
    Initializes the browser using Playwright with headless or non-headless mode.
    Returns the browser context and page object.
"""
async def init_browser(headless=True):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context(viewport={"width": 1200, "height": 800})
    page = await context.new_page()
    # Block images, styles, fonts etc. to speed up scraping
    async def block_resource(route, request):
        if request.resource_type in ["image", "stylesheet", "font"]:
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", block_resource)
    return playwright, browser, page


async def scrape_article(page, url):
    """
        Scrapes the title and content of an article from the given URL.
        Returns a dictionary with 'name', 'link', and 'content'.
    """
    try:
        response = await page.goto(url, wait_until="domcontentloaded")
        if response.status == 403: 
            print(f"HTTP error 403, requests are being blocked, waiting for {sleep_time} seconds before retrying...")
            await asyncio.sleep(sleep_time)  
            response = await page.goto(url, wait_until="domcontentloaded")
            if response.status == 403: 
                print(f"HTTP error 403, requests are being blocked, terminating script for now.")
                raise AccessDenied(url)
        # Extract the title
        title_element = await page.query_selector("h1")
        title = await title_element.inner_text() if title_element else "Untitled"

        # Extract the content
        main_content = await page.query_selector('[data-testid="topic-main-content"]')
        if main_content is None:
            print(f"❌ No main content found at {url}.")
            return None
        content = await element_to_markdown(main_content)
    except:
        print(f"❌ Failed to scrape article at {url}.")
        await asyncio.sleep(sleep_time) 
        return None
    return {
        "name": title.strip(),
        "link": url,
        "content": content
    }


async def element_to_markdown(element):
    children = await element.query_selector_all(":scope > *")
    markdown = ""

    for child in children:
        tag = await child.evaluate('(el) => el.tagName.toLowerCase()')

        if tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag[1])
            heading_text = (await child.inner_text()).strip()
            markdown += f"\n{'#' * level} {heading_text}\n"

        elif tag == "p":
            data_testid = await child.get_attribute("data-testid")
            if data_testid != "topicPara":
                continue
            paragraph = (await child.inner_text()).strip()
            if paragraph:
                markdown += f"{paragraph}\n\n"

        elif tag == "div":
            class_name = (await child.get_attribute("class")) or ""
            data_testid = await child.get_attribute("data-testid")

            # Skip figures or other non-content divs
            if "Figure" in class_name or data_testid == "baseillustrative":
                continue

            # Process inner content as part of current flow
            inner_markdown = await element_to_markdown(child)
            if inner_markdown.strip():
                markdown += inner_markdown + "\n"

        elif tag == "section":
            # Flatten section contents just like any other container
            section_markdown = await element_to_markdown(child)
            if section_markdown.strip():
                markdown += section_markdown + "\n"

    return markdown.strip()

"""
    Main function to launch browser, navigate to site, and run actions.
"""
async def main():
    playwright, browser, page = await init_browser(headless=True)

    size_to_scrape = os.path.getsize('./data/to_scrape.txt')
    if size_to_scrape == 0:
        with open('./data/content_urls.txt', "r", encoding="utf-8") as f:
            urls = set(line.strip() for line in f if line.strip())
    else: 
        with open('./data/to_scrape.txt', "r", encoding="utf-8") as f:
            urls = set(line.strip() for line in f if line.strip())
    to_scrape = set(urls)  # copy to track what still needs to be scraped
    articles = []

    try:
        for i, url in enumerate(tqdm(urls, desc="Scraping articles\n")):
            print('\n')
            #print(f"\nScraping article {i + 1}/{len(urls)}: {url}")
            article = await scrape_article(page, url)
            if not article:
                print(f"⚠️ Failed to scrape article {i + 1}")
                continue
            articles.append(article)
            to_scrape.remove(url)
            #if i%30 == 0:
            #    await asyncio.sleep(sleep_time)  
    except KeyboardInterrupt:
        print("❌ Interrupted by user. Saving progress...")
    except AccessDenied as e:
        print(f"❌ Access denied to {e.url}.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        try:
            with open('./data/to_scrape.txt', "w", encoding="utf-8") as f:
                for url in to_scrape:
                    f.write(url + "\n")
            # Update the merck-articles.json file with the new articles
            if os.path.exists('./data/merck-articles.json'):
                with open('./data/merck-articles.json', "r", encoding="utf-8") as f:
                    merck_articles = json.load(f)
            else:
                merck_articles = []
            merck_articles.extend(articles)
            with open("./data/merck-articles.json", "w", encoding="utf-8") as f:
                json.dump(merck_articles, f, ensure_ascii=False, indent=4)
            print(f"✅ Scraped {len(articles)} new articles. Total: {len(merck_articles)}.")
        except Exception as e:
            print(f"⚠️ Failed to save progress cleanly: {e}")
        finally:
            # Only try to close if initialized
            if browser:
                try:
                    await browser.close()
                except Exception as e:
                    print(f"⚠️ Error while closing browser: {e}")
            if playwright:
                try:
                    await playwright.stop()
                except Exception as e:
                    print(f"⚠️ Error while stopping playwright: {e}")
   
if __name__ == "__main__":
    asyncio.run(main())