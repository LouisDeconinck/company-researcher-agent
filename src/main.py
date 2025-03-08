import os
from apify import Actor
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

class ResponseModel(BaseModel):
    """Automatic Structured response with """
    company_name: str
    company_description: str
    company_website: str
    company_industry: str
    company_location: str
    company_revenue: int
    company_employees: int
    company_founded_year: int
    number_of_actors: int

async def main() -> None:
    await Actor.init()
    await Actor.charge(event_name='init')

    openrouter_api_key = fetch_api_key('OPENROUTER_API_KEY')
    apify_api_key = fetch_api_key('APIFY_API_KEY')
    if not openrouter_api_key or not apify_api_key:
        await Actor.exit()
        
    input = await Actor.get_input()
    company_name = input.get('company_name')
      
    model = OpenAIModel(
        'google/gemini-2.0-flash-exp:free',
        provider=OpenAIProvider(
                base_url='https://openrouter.ai/api/v1', api_key=openrouter_api_key
            ),
    )
    agent = Agent(
        model,
        result_type=ResponseModel,
        system_prompt='You are a company research assistant. You are given a company name and you need to research the company and return the information in the structured format.',
    )
    
    @agent.tool_plain
    async def crawl_website(url: str) -> str:
        """Crawl a website and return the content."""
        Actor.log.info(f"Crawling website: {url}")
        client = Actor.new_client(token=apify_api_key)
        
        run_input = {
            "startUrls": [{ "url": url }],
            "crawlerType": "cheerio",
            "maxCrawlDepth": 1,
            "maxCrawlPages": 10,
        }
        
        try:
            run = await client.actor("apify/website-content-crawler").call(run_input=run_input)
            dataset = await client.dataset(run["defaultDatasetId"]).list_items()
            urls = [item.get('url') for item in dataset.items]
            Actor.log.info(f"Pages crawled: {', '.join(urls)}")
            
            # Combine text content from all crawled pages
            all_text = []
            for item in dataset.items:
                if 'text' in item:
                    all_text.append(item['text'])
            
            if all_text:
                return "\n\n".join(all_text)
            return "No content was found on the website"
            
        except Exception as e:
            Actor.log.error(f"Error crawling website: {str(e)}")
            return f"Failed to crawl website: {str(e)}"
    
    result = await agent.run(f'What is the company "{company_name}" about? Make sure to crawl the website and get the latest information.')  
    
    await Actor.push_data(result.data.model_dump())

    await Actor.exit()

def fetch_api_key(name: str) -> str:
    api_key = os.getenv(name)
    if api_key:
        length = len(api_key)
        Actor.log.info(f"{name}: {api_key[:int(length * 0.1)]}...{api_key[-int(length * 0.1):]}")
        return api_key
    else:
        Actor.log.error(f"Error: {name} is not set in the environment variables.")
        return None
