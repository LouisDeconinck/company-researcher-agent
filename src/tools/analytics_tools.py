from apify import Actor
from typing import Dict, Union, List, Any

async def get_similarweb_results(
    client,
    website: str
) -> Dict[str, Union[str, int, float, List[str], Dict[str, Union[str, int]]]]:
    """Get analytics and company information from Similarweb for a website.

    Args:
        client: The Apify client for making API calls.
        website: Website domain to analyze (e.g., "google.com")
    
    Returns:
        Dictionary containing:
        - name: Company name
        - description: Company description
        - globalRank: Global traffic rank
        - categoryId: Industry category
        - companyYearFounded: Year founded
        - companyName: Legal name
        - companyEmployeesMin/Max: Employee range
        - companyAnnualRevenueMin: Minimum annual revenue
        - companyHeadquarter details: Country code, state, city
        - Traffic metrics: visits, duration, pages/visit, bounce rate
        - Traffic sources and distribution
        - Keywords and referrals
        - Social network distribution
        - Top countries by traffic
        - Competitors and similar sites
        - Demographics: age and gender distribution
    """
    Actor.log.info(f"Getting Similarweb results for website: {website}")
    
    run_input = {
        "websites": [website]
    }
    
    try:
        run = await client.actor("tri_angle/similarweb-scraper").call(run_input=run_input, memory_mbytes=1024)
        dataset = await client.dataset(run["defaultDatasetId"]).list_items()
        
        if dataset.items and len(dataset.items) > 0:
            data = dataset.items[0]
            return {
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "globalRank": data.get("globalRank", 0),
                "categoryId": data.get("categoryId", ""),
                "companyYearFounded": data.get("companyYearFounded", 0),
                "companyName": data.get("companyName", ""), 
                "companyEmployeesMin": data.get("companyEmployeesMin", 0),
                "companyEmployeesMax": data.get("companyEmployeesMax", 0),
                "companyAnnualRevenueMin": data.get("companyAnnualRevenueMin", 0),
                "companyHeadquarterCountryCode": data.get("companyHeadquarterCountryCode", ""),
                "companyHeadquarterStateCode": data.get("companyHeadquarterStateCode", ""),
                "companyHeadquarterCity": data.get("companyHeadquarterCity", ""),
                "avgVisitDuration": data.get("avgVisitDuration", 0),
                "pagesPerVisit": data.get("pagesPerVisit", 0),
                "bounceRate": data.get("bounceRate", 0),
                "totalVisits": data.get("totalVisits", 0),
                "trafficSources": data.get("trafficSources", {}),
                "adsSources": [
                    {
                        "domain": str(a.get("domain", "")),
                        "visitsShare": float(a.get("visitsShare", 0))
                    } for a in data.get("adsSources", []) if a.get("domain")
                ],
                "topKeywords": data.get("topKeywords", []),
                "organicTraffic": data.get("organicTraffic", 0),
                "paidTraffic": data.get("paidTraffic", 0),
                "topReferrals": [
                    {
                        "domain": str(r.get("domain", "")), 
                        "visitsShare": float(r.get("visitsShare", 0))
                    } for r in data.get("topReferrals", []) if r.get("domain")],
                "socialNetworkDistribution": [
                    {
                        "name": str(c.get("name", "")),
                        "visitsShare": float(c.get("visitsShare", 0))
                    } for c in data.get("socialNetworkDistribution", [])
                ],
                "topCountries": [
                    {
                        "country": str(c.get("countryAlpha2Code", "")),
                        "share": float(c.get("visitsShare", 0))
                    } for c in data.get("topCountries", [])
                ],
                "topSimilarityCompetitors": [
                    {
                        "domain": str(c.get("domain", "")), 
                        "visitsTotalCount": int(c.get("visitsTotalCount", 0))
                    } for c in data.get("topSimilarityCompetitors", [])],
                "topInterestedWebsites": [str(w.get("domain", "")) for w in data.get("topInterestedWebsites", [])],
                "ageDistribution": data.get("ageDistribution", {}),
                "maleDistribution": data.get("maleDistribution", 0),
                "femaleDistribution": data.get("femaleDistribution", 0),        
            }
        else:
            Actor.log.warning(f"No Similarweb data retrieved for {website}")
            return {}
        
    except Exception as e:
        Actor.log.error(f"Error fetching Similarweb data for {website}: {str(e)}")
        return {} 