from langchain_core.runnables import Runnable
from tools.scraper import scrape_indeed_jobs

class JobDiscoveryAgent(Runnable):
    def invoke(self, input: dict, config=None) -> list:
        query = input.get("query", "")
        location = input.get("location", "remote")
        print(f"🔍 Searching for: {query} in {location}")
        jobs = scrape_indeed_jobs(query, location)
        return {"jobs": jobs}
