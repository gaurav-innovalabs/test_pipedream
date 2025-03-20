import httpx
from fastapi import FastRouter, HTTPException, Query, Request, Path
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

router = FastRouter(title="Pipedream REST API Proxy")

templates = Jinja2Templates(directory="templates")

# Replace with your actual OAuth App ID from Pipedream for Notion
BASE_URL = "https://api.pipedream.com/v1"
OAUTH_APP_ID = os.getenv("PIPEDREAM_API_TOKEN")
PIPEDREAM_API_HOST = os.getenv("PIPEDREAM_API_HOST", "https://api.pipedream.com")

# Retrieve Pipedream API token from environment
API_TOKEN = os.getenv("PIPEDREAM_API_TOKEN")
CLIENT_ID = os.getenv("PIPEDREAM_CLIENT_ID")
CLIENT_SECRET = os.getenv("PIPEDREAM_CLIENT_SECRETS")

if not API_TOKEN:
    raise Exception("PIPEDREAM_API_TOKEN not set in environment")

def proxy_get(endpoint: str, params: dict = None,environment: str|None=None):
    """
    Helper function to perform a GET request to the Pipedream API.
    """
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }
    if environment:
        headers["X-PD-Environment"] = environment
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


# Add endpoints for Notion actions using Pipedream API
@router.get("/notion/databases")
def list_notion_databases():
    """
    Fetches a list of Notion databases accessible via Pipedream.
    """
    return proxy_get("/apps/notion/databases")


@router.get("/notion/databases/{database_id}/query")
def query_notion_database(database_id: str, filter: str = Query(None)):
    """
    Queries a specific Notion database with optional filters.
    """
    endpoint = f"/apps/notion/databases/{database_id}/query"
    params = {}
    if filter:
        params["filter"] = filter
    return proxy_get(endpoint, params=params)


@router.get("/notion/pages/{page_id}")
def get_notion_page(page_id: str):
    """
    Fetches a specific Notion page by page ID.
    """
    endpoint = f"/apps/notion/pages/{page_id}"
    return proxy_get(endpoint)


@router.post("/notion/pages")
def create_notion_page(database_id: str, page_title: str):
    """
    Creates a new page in a specified Notion database.
    """
    endpoint = f"/apps/notion/pages"
    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {"content": page_title}
                    }
                ]
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}{endpoint}"
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.patch("/notion/pages/{page_id}")
def update_notion_page(page_id: str, new_title: str):
    """
    Updates the title of a Notion page.
    """
    endpoint = f"/apps/notion/pages/{page_id}"
    payload = {
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {"content": new_title}
                    }
                ]
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}{endpoint}"
    response = requests.patch(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.delete("/notion/pages/{page_id}")
def delete_notion_page(page_id: str):
    """
    Deletes or archives a Notion page (depending on Notion API capability).
    """
    endpoint = f"/apps/notion/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}{endpoint}"
    # Notion API archives pages rather than deletes
    payload = {"archived": True}
    response = requests.patch(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
