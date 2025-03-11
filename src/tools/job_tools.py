from apify import Actor
from typing import List, Dict, Union, Optional

async def get_indeed_jobs(
    client,
    indeed_company_url: str,
    max_items_per_search: int = 10
) -> List[Dict[str, Union[str, int, List[str], None]]]:
    """Get job listings from an Indeed.com company page URL.

    Args:
        client: The Apify client for making API calls.
        indeed_company_url: The Indeed.com URL to fetch job listings from. Must be in format indeed.com/cmp/company-name. Do not use a search url.
        max_items_per_search: Maximum number of job listings to fetch (default: 10)
    
    Returns:
        A list of dictionaries containing job details such as position name, job type, location, etc.
    """
    Actor.log.info(f"Getting Indeed jobs from URL: {indeed_company_url}")

    # Verify URL is in correct format
    if ("indeed.com/cmp/" not in indeed_company_url):
        Actor.log.error(f"Invalid Indeed URL format. Must be indeed.com/cmp/company-name. Got: {indeed_company_url}")
        return []
    
    # Ensure the URL ends with /jobs as per the requirement
    if not indeed_company_url.endswith("/jobs"):
        indeed_company_url = f"{indeed_company_url}/jobs"
    
    run_input = {
        "startUrls": [
            {
                "url": indeed_company_url,
                "method": "GET"
            }
        ],
        "maxItemsPerSearch": max_items_per_search,
    }

    try:
        run = await client.actor("misceres/indeed-scraper").call(run_input=run_input, memory_mbytes=256)
        dataset = await client.dataset(run["defaultDatasetId"]).list_items()

        if dataset.items and len(dataset.items) > 0:
            # Filter and format relevant fields for the company research agent
            jobs = []
            for item in dataset.items:
                job = {
                    "positionName": item.get("positionName"),
                    "jobType": item.get("jobType"),
                    "location": item.get("location"),
                    "salary": item.get("salary"),
                    "company": item.get("company"),
                    "url": item.get("url"),
                    "postedAt": item.get("postedAt"),
                    "description": item.get("description")
                }
                jobs.append(job)
            return jobs
        return []

    except Exception as e:
        Actor.log.error(f"Error fetching Indeed jobs: {str(e)}")
        return [] 