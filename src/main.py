from typing import Any, Dict, List, Union
from datetime import datetime, timezone
from apify import Actor
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from dotenv import load_dotenv

from .models import ResponseModel
from .utils import fetch_api_key
from .validators import validate_company_report
from .prompts import get_company_research_prompt
from .tools import (
    crawl_website,
    search_google,
    search_google_maps,
    get_linkedin_company_profile,
    get_indeed_jobs,
    get_trustpilot_reviews,
    get_similarweb_results
)

load_dotenv()

async def main() -> None:
    await Actor.init()
    await Actor.charge(event_name='init')

    apify_api_key = fetch_api_key('APIFY_API_KEY')
    if not apify_api_key:
        await Actor.exit()

    input = await Actor.get_input()
    company_name = input.get('company_name')
    additional_context = input.get('additional_context')

    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    client = Actor.new_client(token=apify_api_key)

    try:
        model = GeminiModel('gemini-2.0-flash', provider='google-gla')

        # Get system prompt from prompts module
        system_prompt = get_company_research_prompt(company_name, additional_context, current_date)

        agent = Agent(
            model=model,
            result_type=ResponseModel,
            system_prompt=system_prompt
        )

        # Register the result validator
        agent.result_validator(validate_company_report)

        # Register all the tools
        @agent.tool_plain
        async def tool_crawl_website(url: str, max_crawl_depth: int = 1, max_crawl_pages: int = 10) -> Dict[str, Union[List[Dict[str, str]], str]]:
            """Crawl a website and return the content.

            Args:
                client: The Apify client for making API calls.
                url: The URL of the website to crawl.
                max_crawl_depth: Maximum depth of links to follow (0 = only start URLs).
                max_crawl_pages: Maximum number of pages to crawl.

            Returns:
                A list of dictionaries containing url, title, and markdown content for each crawled page.
            """
            if not url:
                return {"error": "URL is required"}

            try:
                results = await crawl_website(client, url, max_crawl_depth, max_crawl_pages)
                
                # Charge per result
                if results:
                    await Actor.charge(event_name='result-item', count=len(results))
                
                return {"results": results}
            except Exception as e:
                Actor.log.error(f"Error crawling website: {str(e)}")
                return {"error": str(e)}

        @agent.tool_plain
        async def tool_search_google(query: str, max_results: int = 10) -> Dict[str, Union[List[Dict[str, str]], str]]:
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
            if not query:
                return {"error": "Query is required"}

            try:
                search_results = await search_google(client, query, max_results)
                
                # Charge per result
                if search_results:
                    await Actor.charge(event_name='result-item', count=len(search_results))
                
                return {"results": search_results}
            except Exception as e:
                Actor.log.error(f"Error searching Google: {str(e)}")
                return {"error": str(e)}

        @agent.tool_plain
        async def tool_search_google_maps(query: str, max_reviews: int = 10) -> Dict[str, Union[List[Dict[str, str]], str]]:
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
            if not query:
                return {"error": "Query is required"}

            try:
                search_results = await search_google_maps(client, query, max_reviews)
                
                # Charge per result
                if search_results:
                    await Actor.charge(event_name='result-item', count=len(search_results))
                
                return {"results": search_results}
            except Exception as e:
                Actor.log.error(f"Error searching Google Maps: {str(e)}")
                return {"error": str(e)}

        @agent.tool_plain
        async def tool_get_linkedin_company_profile(linkedin_company_url: str) -> Dict[str, Union[Dict[str, str], str]]:
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
            if not linkedin_company_url:
                return {"error": "LinkedIn company URL is required"}

            try:
                profile = await get_linkedin_company_profile(client, linkedin_company_url)
                
                # Charge for successful profile retrieval
                if profile and not profile.get("error"):
                    await Actor.charge(event_name='result-item', count=1)
                    
                return {"result": profile}
            except Exception as e:
                Actor.log.error(f"Error getting LinkedIn profile: {str(e)}")
                return {"error": str(e)}

        @agent.tool_plain
        async def tool_get_indeed_jobs(indeed_company_url: str, max_items_per_search: int = 10) -> Dict[str, Union[List[Dict[str, str]], str]]:
            """Get job listings from an Indeed.com company page URL.

            Args:
                client: The Apify client for making API calls.
                indeed_company_url: The Indeed.com URL to fetch job listings from. Must be in format indeed.com/cmp/company-name. Do not use a search url.
                max_items_per_search: Maximum number of job listings to fetch (default: 10)
            
            Returns:
                A list of dictionaries containing job details such as position name, job type, location, etc.
            """
            if not indeed_company_url:
                return {"error": "Indeed company URL is required"}

            try:
                job_listings = await get_indeed_jobs(client, indeed_company_url, max_items_per_search)
                
                # Charge per result
                if job_listings:
                    await Actor.charge(event_name='result-item', count=len(job_listings))
                
                return {"results": job_listings}
            except Exception as e:
                Actor.log.error(f"Error getting Indeed jobs: {str(e)}")
                return {"error": str(e)}

        @agent.tool_plain
        async def tool_get_similarweb_results(website: str) -> Dict[str, Union[Dict[str, Any], str]]:
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
            if not website:
                return {"error": "Website is required"}

            try:
                domain_stats = await get_similarweb_results(client, website)
                
                # Charge for successful stats retrieval
                if domain_stats and not domain_stats.get("error"):
                    await Actor.charge(event_name='result-item', count=1)
                    
                return {"result": domain_stats}
            except Exception as e:
                Actor.log.error(f"Error getting SimilarWeb stats: {str(e)}")
                return {"error": str(e)}

        @agent.tool_plain
        async def tool_get_trustpilot_reviews(company_domain: str, max_reviews: int = 10) -> Dict[str, Union[List[Dict[str, str]], str]]:
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
            if not company_domain:
                return {"error": "Company domain is required"}

            try:
                reviews = await get_trustpilot_reviews(client, company_domain, max_reviews)
                
                # Charge per result
                if reviews:
                    await Actor.charge(event_name='result-item', count=len(reviews))
                
                return {"results": reviews}
            except Exception as e:
                Actor.log.error(f"Error getting Trustpilot reviews: {str(e)}")
                return {"error": str(e)}

        result = await agent.run(company_name)
        
        # Save full result to dataset
        await Actor.push_data(result.data.model_dump())
        
        # Save report as markdown file in KV store
        default_kv_store = await Actor.open_key_value_store()
        sanitized_company_name = company_name.lower().replace(' ', '_').replace('.', '_').replace(',', '').replace('&', 'and')
        report_filename = f"{sanitized_company_name}_report.md"
        
        # Log the saving operation
        Actor.log.info(f"Saving report as markdown file: {report_filename}")
        
        # Create basic report header
        report_header = [
            f"# {company_name} Business Report",
            "",
            f"*Generated on: {current_date}*",
            "",
            "---",
            ""
        ]
        
        try:
            # Get the report content from the result
            report_content = result.data.report if hasattr(result.data, 'report') else str(result.data)
            
            # Combine header and content
            enhanced_report = "\n".join(report_header) + report_content
            
        except Exception as e:
            Actor.log.error(f"Error processing report: {str(e)}")
            # Fallback to raw data if report processing fails
            enhanced_report = f"# {company_name} Business Report\n\n*Generated on: {current_date}*\n\n---\n\n{str(result.data)}"
        
        # Save the report content to KV store with explicit content type
        await default_kv_store.set_value(
            report_filename,
            enhanced_report,
            content_type="text/markdown"
        )
        
        # Charge for token usage from the result
        usage = result.usage()
        if usage and usage.total_tokens > 0:
            await Actor.charge(event_name='llm-tokens', count=usage.total_tokens)
            Actor.log.info(f"Charged for {usage.total_tokens} tokens")
    except Exception as e:
        Actor.log.error(f"An error occurred: {str(e)}")
        raise
    finally:
        await Actor.exit()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
