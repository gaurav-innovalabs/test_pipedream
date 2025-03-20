import os
from dotenv import load_dotenv
load_dotenv()

# Environment variables and constants
PIPEDREAM_PROJECT_ID = os.getenv("PIPEDREAM_PROJECT_ID")
PIPEDREAM_PROJECT_ENVIRONMENT = os.getenv("PIPEDREAM_PROJECT_ENVIRONMENT", "development")
PIPEDREAM_API_HOST = os.getenv("PIPEDREAM_API_HOST", "https://api.pipedream.com")
API_TOKEN = os.getenv("PIPEDREAM_API_TOKEN")
OAUTH_TOKEN=os.getenv("PIPEDREAM_OAUTH_TOKEN")
CLIENT_ID = os.getenv("PIPEDREAM_CLIENT_ID")
CLIENT_SECRET = os.getenv("PIPEDREAM_CLIENT_SECRETS")

if not API_TOKEN:
    raise Exception("PIPEDREAM_API_TOKEN not set in environment")

BASE_URL = f"{PIPEDREAM_API_HOST}/v1"