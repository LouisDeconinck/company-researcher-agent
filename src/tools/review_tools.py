from apify import Actor
from typing import List, Dict, Union

async def get_trustpilot_reviews(
    client,
    company_domain: str,
    max_reviews: int = 10
) -> List[Dict[str, Union[str, int, float]]]:
    """Get reviews from Trustpilot for a website.

    Args:
        client: The Apify client for making API calls.
        company_domain: Domain name of the company (e.g., "apify.com")
        max_reviews: Maximum number of reviews to return (default: 10)

    Returns:
        List of review objects with:
        - reviewUrl: Unique review ID
        - authorName: Name of reviewer
        - datePublished: Review publish date
        - reviewHeadline: Review title
        - reviewBody: Full review text
        - reviewLanguage: Language code
        - ratingValue: Rating (1-5)
        - verificationLevel: Verification status
        - numberOfReviews: Number of reviews by author
        - consumerCountryCode: Reviewer country
        - experienceDate: Date of experience
        - likes: Number of likes
    """
    Actor.log.info(f"Getting Trustpilot reviews for company: {company_domain} (max {max_reviews} reviews)")
    
    run_input = {
        "companyDomain": company_domain,
        "count": max_reviews
    }
    
    try:
        run = await client.actor("nikita-sviridenko/trustpilot-reviews-scraper").call(run_input=run_input, memory_mbytes=1024)
        dataset = await client.dataset(run["defaultDatasetId"]).list_items()
        
        if dataset.items:
            reviews = []
            for item in dataset.items:
                review = {
                    "reviewUrl": str(item.get("reviewUrl", "")),
                    "authorName": str(item.get("authorName", "")),
                    "datePublished": str(item.get("datePublished", "")),
                    "reviewHeadline": str(item.get("reviewHeadline", "")),
                    "reviewBody": str(item.get("reviewBody", "")),
                    "reviewLanguage": str(item.get("reviewLanguage", "")),
                    "ratingValue": int(item.get("ratingValue", 0)),
                    "verificationLevel": str(item.get("verificationLevel", "")),
                    "numberOfReviews": int(item.get("numberOfReviews", 0)),
                    "consumerCountryCode": str(item.get("consumerCountryCode", "")),
                    "experienceDate": str(item.get("experienceDate", "")),
                    "likes": int(item.get("likes", 0))
                }
                reviews.append(review)
            return reviews
        else:
            Actor.log.warning(f"No Trustpilot reviews retrieved for {company_domain}")
            return []
        
    except Exception as e:
        Actor.log.error(f"Error fetching Trustpilot reviews for {company_domain}: {str(e)}")
        return [] 