from fastapi import FastAPI, HTTPException, Query
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Pipedream REST API Proxy")

# Retrieve Pipedream API token from environment
API_TOKEN = os.getenv("PIPEDREAM_API_TOKEN")
if not API_TOKEN:
    raise Exception("PIPEDREAM_API_TOKEN not set in environment")

# Base URL for the Pipedream API
BASE_URL = "https://api.pipedream.com/v1"

# Standard headers for authentication
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

def proxy_get(endpoint: str, params: dict = None):
    """
    Helper function to perform a GET request to the Pipedream API.
    """
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/")
def root():
    return {"message": "Pipedream REST API Proxy via FastAPI"}

# --- Workflows Endpoints ---
@app.get("/workflows")
def list_workflows(
    limit: int = Query(None, description="Maximum number of workflows to return."),
    offset: int = Query(None, description="Pagination offset."),
    sort: str = Query(None, description="Field to sort by."),
    order: str = Query(None, description="Sort order: 'asc' or 'desc'."),
    q: str = Query(None, description="Search query for workflows."),
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
    return proxy_get("/workflows", params=params)

@app.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str):
    return proxy_get(f"/workflows/{workflow_id}")

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

# --- Sources Endpoints ---
@app.get("/sources")
def list_sources(
    limit: int = Query(None, description="Maximum number of sources to return."),
    offset: int = Query(None, description="Pagination offset.")
):
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return proxy_get("/sources", params=params)

@app.get("/sources/{source_id}")
def get_source(source_id: str):
    return proxy_get(f"/sources/{source_id}")

# --- Workflow Runs Endpoints ---
@app.get("/workflow_runs")
def list_workflow_runs(
    limit: int = Query(None, description="Maximum number of workflow runs to return."),
    offset: int = Query(None, description="Pagination offset.")
):
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return proxy_get("/workflow_runs", params=params)

@app.get("/workflow_runs/{run_id}")
def get_workflow_run(run_id: str):
    return proxy_get(f"/workflow_runs/{run_id}")

# --- Events Endpoints ---
@app.get("/events")
def list_events(
    limit: int = Query(None, description="Maximum number of events to return."),
    offset: int = Query(None, description="Pagination offset.")
):
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return proxy_get("/events", params=params)

@app.get("/events/{event_id}")
def get_event(event_id: str):
    return proxy_get(f"/events/{event_id}")

# --- Logs Endpoints ---
@app.get("/logs")
def list_logs(
    limit: int = Query(None, description="Maximum number of logs to return."),
    offset: int = Query(None, description="Pagination offset.")
):
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return proxy_get("/logs", params=params)

@app.get("/logs/{log_id}")
def get_log(log_id: str):
    return proxy_get(f"/logs/{log_id}")

# --- Profile Endpoint ---
@app.get("/profile")
def get_profile():
    return proxy_get("/profile")

# --- Organizations Endpoint ---
@app.get("/organizations")
def list_organizations(
    limit: int = Query(None, description="Maximum number of organizations to return."),
    offset: int = Query(None, description="Pagination offset.")
):
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return proxy_get("/organizations", params=params)
