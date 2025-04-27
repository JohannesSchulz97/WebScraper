# WebScraping the Merck Veterinary Manual with Playwright

As part of the project of creating a **veterinary assistant chatbot powered by Retrieval-Augmented Generation (RAG)**, 
this codebase is designed to create a dataset of high-quality veterinary science articles by scraping 
the **Merck Veterinary Manual**—a well-respected and freely accessible resource in the field of veterinary science.
As Merck does not offer a public **API**, this is the only way to retrieve their content 

## Installation of Dependencies

Besides a working python installation, this project requires the playwright and tqdm packages.
You can use `conda env create -f environment.yml -n myenvname` to install them, 
replacing myenvname with the name you want to give your new conda virtual environment.

## Web Scraping


I decided to implement the Web Scraping with python and the **Playwright** package, a modern alternative to **Selenium** 
that is particularly useful when scraping websites that load their content dynamically via JavaScript. 
Playwright allows for automated interaction with the browser, enabling robust scraping even from complex web applications. 
In addition to that, it is one of the main tools used to enable LLM powered agents to act in the web, meaning that it is generally useful to know.

In a nutshell, **Playwright** launches a Chromium browser which can then be used to created a new `Context` and `Page` object.

``` python
async def init_browser(headless=True):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context(viewport={"width": 1200, "height": 800})
    page = await context.new_page()
    return playwright, browser, page
```
Through the page, we can for example:

- navigate to a URL (`await page.goto(current_url, wait_until="domcontentloaded")`
- retrieve HTML content (`await page.query_selector('[data-testid="topic-main-content"]')`) 
* or interact with the website (`await button.click()`)

### Content URL Retrieval
Given the huge amount of information in the form of articles, videos, quizzes, etc. I decided to first retrieve of all the URLs containing actual written content.

This [webcrawler](https://github.com/JohannesSchulz97/WebScraper/blob/main/crawler.py) operates in a loop, at any point in time maintaining three sets of URLs:

- `visited.txt` — URLs that have already been processed  
- `to_explore.txt` — URLs yet to be visited  
- `content_urls.txt` — URLs confirmed to contain article content  

This is mostly done so that progess is not lost if the script is being interrupted due to whatever reason.
The simplified structure of the core logic looks like this, resembling DFS or BFS except the fact that we operate on sets, so any order is lost:

```python
while to_explore:
    current_url = to_explore.pop()
    if current_url in visited:
        continue
    response = await page.goto(current_url)
    if response.status == 403:
        raise AccessDenied(current_url)
    if await page.query_selector('[data-testid="topic-main-content"]'):
        content_urls.append(current_url)
    else:
        found_urls = await find_urls(page)
        to_explore.update([url for url in found_urls if url not in visited])
    visited.add(current_url)
```
Any URL we visit, will either be an overview page, linking to further subpages or it will be containing an actual article about some topic, indicated by the the attribute `data-testid=topic-main-content`.

### Scraping Article Content

Once we’ve retrieved the list of article URLs using our crawler, the next step is to extract the actual content. For this, we use a dedicated [`scraper.py`](https://github.com/JohannesSchulz97/WebScraper/blob/main/scraper.py) script:

``` python
async def main():
	...
	for i, url in enumerate(tqdm(urls, desc="Scraping articles\n")):
	    ...
	    article = await scrape_article(page, url)
		 ...
	    articles.append(article)
	    to_scrape.remove(url)
	...
	with open('./data/merck-articles.json', "r", encoding="utf-8") as f:
	     merck_articles = json.load(f)
	...
	merck_articles.extend(articles)
	with open("./data/merck-articles.json", "w", encoding="utf-8") as f:
	    json.dump(merck_articles, f, ensure_ascii=False, indent=4)
```

At its core, the scraper visits each URL in the `content_urls.txt` file, retrieves its title and the article content as Markdown code and finally stores the articles in `merck-articles.json`.

``` python
	async def scrape_article(page, url):
	...
	response = await page.goto(url, wait_until="domcontentloaded")
	...
	title_element = await page.query_selector("h1")
	title = await title_element.inner_text() if title_element else "Untitled"
	
	# Extract the content
	main_content = await page.query_selector('[data-testid="topic-main-content"]')
	...
	return {
		"name": title.strip(),
		"link": url,
		"content": content
	}

```
After scraping the Merck Veterinary Manual website, we end 19.7 MB of data made up of ~3000 individual articles and a total of 2836584 words. 
The dataset is freely available [here](https://raw.githubusercontent.com/JohannesSchulz97/WebScraper/refs/heads/main/data/merck-articles.json).


