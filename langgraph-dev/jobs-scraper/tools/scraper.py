from playwright.sync_api import sync_playwright

def scrape_indeed_jobs(query: str, location: str = "remote", max_results: int = 5):
    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        search_url = f"https://www.indeed.com/jobs?q={query}&l={location}"
        page.goto(search_url)
        page.wait_for_selector(".job_seen_beacon", timeout=10000)

        listings = page.query_selector_all(".job_seen_beacon")[:max_results]
        for job in listings:
            title = job.query_selector("h2").inner_text() if job.query_selector("h2") else ""
            company = job.query_selector(".companyName").inner_text() if job.query_selector(".companyName") else ""
            location = job.query_selector(".companyLocation").inner_text() if job.query_selector(".companyLocation") else ""
            link = job.query_selector("a").get_attribute("href")
            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "url": f"https://indeed.com{link}" if link else ""
            })

        browser.close()
    return jobs
