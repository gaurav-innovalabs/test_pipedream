from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from fastapi.responses import JSONResponse
from app.config import PIPEDREAM_API_HOST, OAUTH_TOKEN, PIPEDREAM_PROJECT_ID, PIPEDREAM_PROJECT_ENVIRONMENT, CLIENT_ID, CLIENT_SECRET, BASE_URL
from app.helpers import proxy_get

routes = APIRouter(tags=["Accounts"])

@routes.get("/accounts", response_class=JSONResponse)
async def get_accounts(
        app: Optional[str] = Query(
            None,
            description=(
                    "The ID or name slug of the app you'd like to retrieve. "
                    "For example, Slack's unique app ID is app_OkrhR1, and its name slug is slack.\n\n"
                    "You can find the app's ID in the response from the List apps endpoint, and the name slug under the Authentication section of any app page."
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
    

@routes.get("/connect/{project_id}/accounts/{account_id}")
def get_account_details(
    project_id: str,
    account_id: str,
    app: str = Query(None, description="Filter by app"),
    external_user_id: str = Query(None, description="Filter by external user ID"),
    include_credentials: bool = Query(False, description="Include credentials in the response")
):
    """
    Retrieve account details for a specific account based on the account ID.

    **Path Parameters:**
    - `project_id` (str): The project's ID.
    - `account_id` (str): The ID of the account you want to retrieve.

    **Query Parameters (Optional):**
    - `app` (str): Filter by app.
    - `external_user_id` (str): Filter by external user ID.
    - `include_credentials` (bool): Include credentials in the response when set to true.
    """
    params = {}
    if app:
        params["app"] = app
    if external_user_id:
        params["external_user_id"] = external_user_id
    if include_credentials:
        params["include_credentials"] = "true"

    endpoint = f"/connect/{project_id}/accounts/{account_id}"
    return proxy_get(endpoint, params=params)
