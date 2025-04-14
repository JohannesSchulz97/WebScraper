"""

import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.msdvetmanual.com/dog-owners')

soup = BeautifulSoup(r.content, 'html.parser')
contents = soup.find('div', class_='Section_leftContent__vp_sT')
links = [a['href'] for a in contents.find_all('a', href=True)]

with open('output.txt', 'w') as file:
    print(links, file=file)
"""
"""
import requests
from bs4 import BeautifulSoup

# Fetch the page
r = requests.get('https://www.msdvetmanual.com/dog-owners')

# Parse the content
soup = BeautifulSoup(r.content, 'html.parser')

# Find the container
contents = soup.find('div', class_='Section_leftContent__vp_sT')
print(contents.prettify())

# Check if contents is found
if contents:
    links = [a['href'] for a in contents.find_all('a', href=True)]
else:
    links = ["No content found"]





# Write to file
with open('output.txt', 'w') as file:
    print(links, file=file)
"""

"""
import requests
from bs4 import BeautifulSoup
import json
from tqdm import tqdm
import time

BASE_URL = "https://www.merckvetmanual.com"
START_URL = BASE_URL + "/dog-owners"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def get_article_links(start_url):
    res = requests.get(start_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Find links inside the dog section
    links = soup.select("a[href^='/dog-owners']")  # all internal dog articles
    article_links = list({BASE_URL + a['href'] for a in links if a['href'].count("/") > 2})
    return article_links

def scrape_article(url):
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Untitled"

    content_div = soup.find("div", class_="content-box") or soup.find("div", id="article-body")
    paragraphs = content_div.find_all("p") if content_div else []
    text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    return {
        "title": title,
        "url": url,
        "content": text
    }

def main():
    print("Fetching article links...")
    links = get_article_links(START_URL)
    print(f"Found {len(links)} articles.")

    data = []
    for url in tqdm(links):
        try:
            article = scrape_article(url)
            if len(article["content"]) > 100:  # ignore very short ones
                data.append(article)
            time.sleep(1)  # be polite to their servers
        except Exception as e:
            print(f"Failed to process {url}: {e}")

    with open("merck_dog_articles.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Done! Saved {len(data)} articles to merck_dog_articles.json")

if __name__ == "__main__":
    main()
"""


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

def init_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    # Prevent Selenium Manager bug by explicitly passing a working driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def expand_all(driver):
    wait = WebDriverWait(driver, 10)
    while True:
        try:
            plus_buttons = driver.find_elements(By.CSS_SELECTOR, ".icon-plus")
            if not plus_buttons:
                print("All sections expanded.")
                break
            for btn in plus_buttons:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(10)
                except Exception as e:
                    print(f"Error clicking button: {e}")
                    continue
        except Exception as e:
            print(f"Error finding buttons: {e}")
            break


def get_article_links(driver):
    toc_url = "https://www.merckvetmanual.com/dog-owners"
    driver.get(toc_url)
    expand_all(driver)
    time.sleep(2)

    # After expansion, get all links to actual articles
    links = driver.find_elements(By.CSS_SELECTOR, "#toc a[href*='/']")
    hrefs = list(set(link.get_attribute("href") for link in links if "/all-" not in link.get_attribute("href")))
    return hrefs


def scrape_article(driver, url):
    driver.get(url)
    time.sleep(1.5)

    try:
        title_elem = driver.find_element(By.TAG_NAME, "h1")
        content_elem = driver.find_element(By.CSS_SELECTOR, ".content-section")
        title = title_elem.text.strip()
        content = content_elem.text.strip()
        return {"url": url, "title": title, "content": content}
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return None


def main():
    driver = init_driver(headless=False)
    articles = []

    try:
        print("Getting article links...")
        links = get_article_links(driver)
        print(f"Found {len(links)} articles")

        for i, link in enumerate(links):
            print(f"Scraping {i+1}/{len(links)}: {link}")
            data = scrape_article(driver, link)
            if data:
                articles.append(data)

    finally:
        driver.quit()

    # Save to local file
    os.makedirs("data", exist_ok=True)
    with open("data/merck_articles.txt", "w", encoding="utf-8") as f:
        for article in articles:
            f.write(f"{article['title']}\n{article['url']}\n{article['content']}\n{'='*80}\n")

    print("Scraping complete. Articles saved to data/merck_articles.txt")


if __name__ == "__main__":
    main()