import os
from apify import Actor

def fetch_api_key(name: str) -> str:
    """
    Fetch an API key from environment variables.
    
    Args:
        name: The name of the environment variable containing the API key.
        
    Returns:
        The API key as a string.
    """
    api_key = os.getenv(name)
    if api_key:
        length = len(api_key)
        Actor.log.info(
            f"{name}: {api_key[:int(length * 0.1)]}...{api_key[-int(length * 0.1):]}")
        return api_key
    else:
        Actor.log.error(
            f"Error: {name} is not set in the environment variables.")
        return "" 