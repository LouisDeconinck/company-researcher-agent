import os
from apify import Actor
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
load_dotenv()

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
        system_prompt='Be concise, reply with one sentence.',
    )
    
    result = await agent.run(f'What is the company "{company_name}" about?')  
    print(result.data)
    
    await Actor.push_data(
        {
            'response': result.data,
        }
    )

    await Actor.exit()
    
def fetch_api_key(name: str) -> str:
    api_key = os.getenv(name)
    if api_key:
        length = len(api_key)
        print(f"{name}: {api_key[:int(length * 0.1)]}...{api_key[-int(length * 0.1):]}")
        return api_key
    else:
        print(f"Error: {name} is not set in the environment variables.")
        return None
