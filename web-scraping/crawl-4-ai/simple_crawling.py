import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def main():
    browser_config = BrowserConfig()  
    run_config = CrawlerRunConfig(
        word_count_threshold=10,
        exclude_external_links=True,
        remove_overlay_elements=True,
        process_iframes=True
        )  

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )
        print(result.html)  # Raw HTML
        print(result.cleaned_html) # Cleaned HTML
        print(result.markdown.raw_markdown) # Raw markdown from cleaned html
        print(result.markdown.fit_markdown) # Most relevant content in markdown

        print(result.success)      # True if crawl succeeded
        print(result.status_code)  # HTTP status code (e.g., 200, 404)

        print(result.media)        # Dictionary of found media (images, videos, audio)
        print(result.links)        # Dictionary of internal and external links

if __name__ == "__main__":
    asyncio.run(main())
