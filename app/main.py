import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uuid
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

load_dotenv()

PIPEDREAM_PROJECT_ID = os.getenv("PIPEDREAM_PROJECT_ID")
PIPEDREAM_PROJECT_ENVIRONMENT = os.getenv("PIPEDREAM_PROJECT_ENVIRONMENT", "development")

app = FastAPI(title="Pipedream REST API Proxy")

templates = Jinja2Templates(directory="templates")

# Replace with your actual OAuth App ID from Pipedream for Notion
OAUTH_APP_ID = os.getenv("PIPEDREAM_API_TOKEN")
PIPEDREAM_API_HOST = os.getenv("PIPEDREAM_API_HOST", "https://api.pipedream.com")

# Retrieve Pipedream API token from environment
API_TOKEN = os.getenv("PIPEDREAM_API_TOKEN")
CLIENT_ID = os.getenv("PIPEDREAM_CLIENT_ID")
CLIENT_SECRET = os.getenv("PIPEDREAM_CLIENT_SECRETS")

if not API_TOKEN:
    raise Exception("PIPEDREAM_API_TOKEN not set in environment")

# Base URL for the Pipedream API
BASE_URL = "https://api.pipedream.com/v1"


def proxy_get(endpoint: str, params: dict = None):
    """
    Helper function to perform a GET request to the Pipedream API.
    """
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Pass the OAuth App ID to the template so it can be used by the frontend
    return templates.TemplateResponse("index.html", {"request": request, "oauth_app_id": OAUTH_APP_ID})


async def server_connect_token_create(external_user_id: str):
    """
    Calls Pipedream's Connect API to generate a short-lived token for the given external user.
    Uses header-based authentication.
    """
    url = f"{BASE_URL}/connect/{PIPEDREAM_PROJECT_ID}/tokens"
    payload = {
        "external_user_id": external_user_id,
        "allowed_origins": [
            "http://localhost:3000",
            "http://localhost:8000",
            "https://example.com"
        ]
    }
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "X-PD-Environment": PIPEDREAM_PROJECT_ENVIRONMENT
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
@app.get("/token")
async def get_token():
    """
    Generates and returns a Pipedream Connect token.
    In production, this token is one-time use and must be freshly generated
    for each connection request.
    """
    external_user_id = str(uuid.uuid4())
    try:
        token_data = await server_connect_token_create(external_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(token_data)

@app.post("/generate-token")
def generate_token():
    token_url = 'https://api.pipedream.com/v1/oauth/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(token_url, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    token_data = response.json()
    return {"access_token": token_data.get('access_token')}

# --- Apps Endpoints ---
@app.get("/apps")
def list_apps(
    limit: int = Query(None, description="Maximum number of apps to return."),
    offset: int = Query(None, description="Pagination offset."),
    sort: str = Query(None, description="Field to sort by."),
    order: str = Query(None, description="Sort order: 'asc' or 'desc'."),
    q: str = Query(None, description="Search query for apps."),
    fields: str = Query(None, description="Comma-separated list of fields to include.")
):
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if sort is not None:
        params["sort"] = sort
    if order is not None:
        params["order"] = order
    if q is not None:
        params["q"] = q
    if fields is not None:
        params["fields"] = fields
    return proxy_get("/apps", params=params)

@app.get("/apps/{app_id}")
def get_app(app_id: str):
    return proxy_get(f"/apps/{app_id}")