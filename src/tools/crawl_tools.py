from apify import Actor

async def crawl_website(
    client,
    url: str,
    max_crawl_depth: int = 1,
    max_crawl_pages: int = 10,
) -> list[dict[str, str]]:
    """Crawl a website and return the content.

    Args:
        client: The Apify client for making API calls.
        url: The URL of the website to crawl.
        max_crawl_depth: Maximum depth of links to follow (0 = only start URLs).
        max_crawl_pages: Maximum number of pages to crawl.

    Returns:
        A list of dictionaries containing url, title, and markdown content for each crawled page.
    """
    run_input = {
        "startUrls": [{"url": url}],
        "crawlerType": "cheerio",
        "maxCrawlDepth": max_crawl_depth,
        "maxCrawlPages": max_crawl_pages,
    }

    Actor.log.info(f"Crawling website: {url}, max depth: {max_crawl_depth}, max pages: {max_crawl_pages}")

    try:
        run = await client.actor("apify/website-content-crawler").call(run_input=run_input, memory_mbytes=1024)
        dataset = await client.dataset(run["defaultDatasetId"]).list_items()

        results = []
        for item in dataset.items:
            if 'url' in item and 'metadata' in item and 'markdown' in item:
                results.append({
                    "url": item['url'],
                    "title": item['metadata']['title'],
                    "markdown": item['markdown']
                })

        return results if results else []

    except Exception as e:
        Actor.log.error(f"Error crawling website: {str(e)}")
        return [] 