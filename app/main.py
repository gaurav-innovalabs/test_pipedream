from fastapi import FastAPI, HTTPException, Query
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Pipedream REST API Proxy")

# Retrieve Pipedream API token from environment
API_TOKEN = os.getenv("PIPEDREAM_API_TOKEN")
CLIENT_ID = os.getenv("PIPEDREAM_CLIENT_ID")
CLIENT_SECRET = os.getenv("PIPEDREAM_CLIENT_SECRET")

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

@app.get("/")
def root():
    return {"message": "Pipedream REST API Proxy via FastAPI"}
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