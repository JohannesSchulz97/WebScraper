import asyncio
import json
from playwright.async_api import async_playwright
from json_tree_viewer import save_structure_to_file
import argparse
import sys


"""
    Initializes the browser using Playwright with headless or non-headless mode.
    Returns the browser context and page object.
"""
async def init_browser(headless=True):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context(viewport={"width": 1200, "height": 800})
    page = await context.new_page()
    return playwright, browser, page

"""
    Tries to accept the cookie banner if it exists on the page.
    Prevents interference with future button clicks.
"""
async def accept_cookies(page):
    try:
        await page.click("#onetrust-accept-btn-handler", timeout=5000)
        print("Accepted cookies.")
        await page.wait_for_timeout(1000)
    except Exception as e:
        print("No cookie banner found or could not click it:", e)


async def scrape_article(page, url):
    """
        Scrapes the title and content of an article from the given URL.
        Returns a dictionary with 'name', 'link', and 'content'.
    """
    try:
        await page.goto(url, wait_until="domcontentloaded")

        # Extract the title
        title_element = await page.query_selector("h1")
        title = await title_element.inner_text() if title_element else "Untitled"

        # Extract the content
        main_content = await page.query_selector('[data-testid="topic-main-content"]')
        content = await element_to_markdown(main_content)

        return {
            "name": title.strip(),
            "link": url,
            "content": content
        }
    except Exception as e:
        print(f"⚠️ Failed to scrape {url}: {e}")
        return None
"""
async def extract_introduction(element):
    children = await element.query_selector_all(':scope > *')
    content = ""
    
    for child in children:
        tag = await child.evaluate('(el) => el.tagName')

        if tag == "SECTION":
            return content.strip()  # Stop at the first section

        elif tag == "P":
            if not await child.get_attribute("data-testid") == "topicPara":
                continue
            text = await child.inner_text()
            text = text.strip()
            if text:
                content += text + "\n"

        elif tag == "DIV":
            data_testid = await element.get_attribute("data-testid")
            class_name = await element.get_attribute("class") or ""
            if "Figure" in class_name or data_testid == "baseillustrative":
                continue
            content += await extract_introduction(child)
    return content.strip()

async def get_element_depth(elem, root):
    return await elem.evaluate(
        "(el, root) => { let d = 0; while (el && el !== root) { d++; el = el.parentElement; } return d; }",
        root
    )


async def parse_element(element, title=None):
    content_dict = {}

    # Optional: Store section title
    if not title: 
        first_heading = await element.query_selector('h1, h2, h3, h4, h5, h6')
        title = (await first_heading.inner_text()).strip() if first_heading else "Untitled"
    content_dict["title"] = title

    # Fix: Await this!
    content_dict["content"] = await extract_introduction(element)

    # Parse subsections recursively
    sections = await element.query_selector_all('section')    
    if not sections:
        return content_dict
    reference_depth = await get_element_depth(sections[0], element)

    for section in sections:
        depth = await get_element_depth(section, element)
        if depth != reference_depth:
            continue
        section_content = await parse_element(section)
        section_title = section_content.get("title", "Untitled Section")
        content_dict[section_title] = section_content

    return content_dict
"""

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

async def save_to_json(data, filename="articles.json"):
    """
        Saves a list of articles to a JSON file.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(data)} articles to {filename}")

"""
    Main function to launch browser, navigate to site, and run actions.
"""
async def main():
    playwright, browser, page = await init_browser(headless=True)

    with open('./data/content_urls.txt', "r", encoding="utf-8") as f:
        urls = set(line.strip() for line in f if line.strip())
    '''
    result = await scrape_article(page, "https://www.merckvetmanual.com/dog-owners/description-and-physical-characteristics-of-dogs/description-and-physical-characteristics-of-dogs")
    with open('test.md', 'w', encoding='utf-8') as f:
        f.write(result['content'])
    print(result)
    return
    '''
    articles = []
    for i, url in enumerate(urls):
        print(f"Scraping article {i + 1}/{len(urls)}: {url}")
        article = await scrape_article(page, url)
        if not article:
            print(f"⚠️ Failed to scrape article {i + 1}")
            continue
        articles.append(article)
        

    await save_to_json(articles, filename=f"test.json")
    save_structure_to_file(f"test.json")

    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())