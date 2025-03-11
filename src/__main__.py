import asyncio
import sys
import os

# Add the parent directory to the path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.main import main

# Execute the Actor entry point.
asyncio.run(main())
