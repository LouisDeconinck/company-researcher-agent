from apify import Actor
from typing import List, Dict, Union, Any

async def search_google(
    client,
    query: str, 
    max_results: int = 10
) -> List[Dict[str, str]]:
    """Get Google search results.

    Args:
        client: The Apify client for making API calls.
        query: The search query. Can be:
              - Simple keywords: "san francisco weather"
              - Specific URL: "https://www.cnn.com"
              - Advanced operators: "function calling site:openai.com"
        max_results: Maximum number of top organic search results to fetch (default: 10).
                    If query is a URL, this parameter is ignored.

    Returns:
        A list of dictionaries containing url, title, and markdown content for each result.
    """
    Actor.log.info(
        f"Searching Google for: {query} (max results: {max_results})")
    run_input = {
        "query": query,
        "maxResults": max_results,
        "scrapingTool": "raw-http",
    }

    try:
        run = await client.actor("apify/rag-web-browser").call(run_input=run_input, memory_mbytes=256)
        dataset = await client.dataset(run["defaultDatasetId"]).list_items()

        results = []
        for item in dataset.items:
            if 'metadata' in item and 'markdown' in item:
                results.append({
                    "url": item['metadata']['url'],
                    "title": item['metadata']['title'],
                    "markdown": item['markdown']
                })

        return results

    except Exception as e:
        Actor.log.error(f"Error fetching search results: {str(e)}")
        return []

async def search_google_maps(
    client,
    query: str, 
    max_reviews: int = 10
) -> List[Dict[str, Union[str, int, Dict[str, Any], List[Any]]]]:
    """Get Google Maps search results focused on company information.

    Args:
        client: The Apify client for making API calls.
        query: The search query for finding a company/business on Google Maps.
              Examples:
              - Company name: "Apify"
              - Company with location: "Microsoft Prague"
              - Office address: "1 Infinite Loop, Cupertino"
        max_reviews: Maximum number of reviews to fetch per place (default: 10).

    Returns:
        A list of dictionaries containing essential company details:
        - title: Company name
        - description: Business description if available
        - categoryName: Primary business category
        - categories: List of all business categories
        - address: Full address
        - street: Street address
        - city: City name
        - postalCode: Postal/ZIP code
        - countryCode: Two-letter country code
        - website: Company website URL
        - phone: Contact phone number
        - location: Dict with lat/lng coordinates
        - totalScore: Average rating (0-5)
        - reviewsCount: Total number of reviews
        - reviewsDistribution: Breakdown of ratings by star count
        - reviews: List of relevant reviews containing:
            - text: Review content (if not null)
            - stars: Rating given (1-5)
            - publishAt: When review was posted
        - additionalInfo: Additional business attributes and amenities
    """
    Actor.log.info(
        f"Searching Google Maps for: {query} (max reviews: {max_reviews})")
    run_input = {
        "searchStringsArray": [query],
        "maxCrawledPlaces": 1,  # We only need the top result
        "maxReviews": max_reviews,
        "language": "en",
    }

    try:
        run = await client.actor("compass/crawler-google-places").call(run_input=run_input, memory_mbytes=1024)
        dataset = await client.dataset(run["defaultDatasetId"]).list_items()

        results = []
        for item in dataset.items:
            # Extract only the fields we need
            place_data = {
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "categoryName": item.get("categoryName", ""),
                "categories": item.get("categories", []),
                "address": item.get("address", ""),
                "street": item.get("street", ""),
                "city": item.get("city", ""),
                "postalCode": item.get("postalCode", ""),
                "countryCode": item.get("countryCode", ""),
                "website": item.get("website", ""),
                "phone": item.get("phone", ""),
                "location": item.get("location", {}),
                "totalScore": item.get("totalScore", 0),
                "reviewsCount": item.get("reviewsCount", 0),
                "reviewsDistribution": item.get("reviewsDistribution", {}),
                "reviews": item.get("reviews", []),
                "additionalInfo": item.get("additionalInfo", {})
            }
            results.append(place_data)

        return results

    except Exception as e:
        Actor.log.error(f"Error fetching Google Maps results: {str(e)}")
        return [] 