from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from fastapi.responses import HTMLResponse, JSONResponse
import os
import requests
router = APIRouter(tags=["Accounts"])

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

def proxy_get(endpoint: str, params: dict = None, environment: str|None = None):
    """
    Helper function to perform a GET request to the Pipedream API.
    """
    headers = {"Authorization": f"Bearer {OAUTH_TOKEN}"}
    if environment:
        headers["X-PD-Environment"] = environment
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
@router.get("/accounts", response_class=JSONResponse)
async def get_accounts(
        app: Optional[str] = Query(
            None,
            description=(
                    "The ID or name slug of the app you'd like to retrieve. "
                    "For example, Slack’s unique app ID is app_OkrhR1, and its name slug is slack.\n\n"
                    "You can find the app’s ID in the response from the List apps endpoint, and the name slug under the Authentication section of any app page."
            )
        ),
        include_credentials: Optional[bool] = Query(
            False,
            description="Pass include_credentials=true as a query-string parameter to include the account credentials in the response."
        )
):
    """
    Retrieve a list of accounts from the Pipedream API.

    ### Parameters:
    - **app**: (optional) The ID or name slug of the app to retrieve accounts for.
    - **oauth_app_id**: (optional) The ID of the custom OAuth app to retrieve accounts for.
    - **include_credentials**: (optional) Include account credentials in the response when set to true.
    """
    params = {}

    if app:
        params["app"] = app
    params["oauth_app_id"] = OAUTH_TOKEN
    if include_credentials:
        params["include_credentials"] = "true"

    try:
        accounts = proxy_get("/accounts", params=params)
        return accounts
    except HTTPException as http_err:
        raise http_err
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))