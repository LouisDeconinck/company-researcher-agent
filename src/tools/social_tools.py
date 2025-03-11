from apify import Actor
from typing import Dict, Any, List

async def get_linkedin_company_profile(
    client,
    linkedin_company_url: str
) -> Dict[str, Any]:
    """Get LinkedIn company profile.

    Args:
        client: The Apify client for making API calls.
        linkedin_company_url: The LinkedIn company URL. E.g. https://www.linkedin.com/company/apple/

    Returns:
        A dictionary containing company details:
        - name: Company name
        - description: Company description
        - industry: Industry
        - employees: Number of employees
        - website: Company website
        - specialties: List of specialties
        - address: Company address details
    """
    Actor.log.info(f"Getting LinkedIn company profile for: {linkedin_company_url}")
    run_input = {
        "linkedinUrls": [linkedin_company_url]
    }

    try:
        run = await client.actor("icypeas_official/linkedin-company-scraper").call(run_input=run_input, memory_mbytes=128)
        dataset = await client.dataset(run["defaultDatasetId"]).list_items()

        if dataset.items and len(dataset.items) > 0:
            item = dataset.items[0]['data'][0]['result']
            return {
                "name": item.get("name"),
                "description": item.get("description"),
                "industry": item.get("industry"),
                "employees": item.get("numberOfEmployees"),
                "website": item.get("website"),
                "specialties": [s["value"] for s in item.get("specialties", [])],
                "address": item.get("address")
            }
        return {}

    except Exception as e:
        Actor.log.error(f"Error fetching LinkedIn company profile: {str(e)}")
        return {} 