import base64
import uuid
import os
import requests
from fastapi import FastAPI, HTTPException, Query, Request, Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.accounts_routes import router as account_routes
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

app = FastAPI(title="Pipedream REST API Proxy")
templates = Jinja2Templates(directory="templates")

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
app.include_router(account_routes)
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "oauth_app_id": OAUTH_TOKEN})
@app.post("/webhook", response_class=HTMLResponse)
async def webhook(request: Request):
    print("--------------------------webhook got the trigger action--------------------------")
    x  = await request.json()
    print(x)
    return JSONResponse({"message": "Webhook triggered successfully!"})
@app.get("/slack", response_class=HTMLResponse)
async def slack_auth(request: Request):
    """
    Render the Slack authentication page.
    """
    return templates.TemplateResponse("slack.html", {"request": request, "oauth_app_id": OAUTH_TOKEN})

async def server_connect_token_create(external_user_id: str):
    """
    Calls Pipedream's Connect API to generate a short-lived token for the given external user.
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
        "Authorization": f"Bearer {OAUTH_TOKEN}",
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
    """
    external_user_id = str(uuid.uuid4())
    try:
        token_data = await server_connect_token_create(external_user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(token_data)

@app.post("/generate-token")
def generate_token():
    """
    Generate an OAuth access token using client credentials.
    """
    token_url = f"{BASE_URL}/oauth/token"
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

@app.get("/connect/{project_id}/actions")
def get_project_actions(
        project_id: str,
        app: str = Query(..., description="The app name to get actions for")
):
    """
    Get list of actions for a specific app in a project.
    """
    params = {"app": app}
    return proxy_get(f"/connect/{project_id}/actions", params=params, environment="development")

@app.get("/connect/{project_id}/components/{action_name}")
def get_more_details_of_action(
        project_id: str,
        action_name: str = Path(..., description="Component name, e.g. gitlab-list-commits",
                                example="gitlab-list-commits", placeholder="gitlab-list-commits")
):
    """
    Get more details of a specific action.
    """
    return proxy_get(f"/connect/{project_id}/components/{action_name}", environment="development")
#
@app.post("/connect/{project_id}/components/{action_name}/run")
def execute_action(
        project_id: str,
        action_name: str = Path(..., description="Component name, e.g. gitlab-list-commits",
                                example="gitlab-list-commits", placeholder="gitlab-list-commits"),
        # external_user_id: str = Query(..., description="External user ID, e.g. abc-123"),
        # prop_name: str = Query(..., description="Property name to configure, e.g. projectId"),
        # configured_props: dict = {}
):
    """
    Execute a specific action for a user.
    """
    url = f"{BASE_URL}/connect/{project_id}/actions/run"
    payload = {
        "external_user_id": "31b294c4-450f-446c-ad4d-c49178f577de",
        "id": "slack-send-message",
        "configured_props": {
          "slack": {
            "authProvisionId": "apn_kVh9AoD"
          }
        },
        "text": "Hello, this is a test message!",
        "conversation": "#test-user",
        "mrkdwn": True,
        "as_user": False
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OAUTH_TOKEN}",
        "X-PD-Environment": "development"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

@app.get("/connect/{project_id}/accounts/{account_id}")
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
    - `project_id` (str): The project’s ID.
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

def encode_url(url: str) -> str:
    """
    URL safe Base64 encode the given URL.
    """
    encoded_bytes = base64.urlsafe_b64encode(url.encode())
    # Remove padding '=' characters if desired
    return encoded_bytes.decode().rstrip("=")

@app.post("/send-slack", summary="Send a Slack message via Pipedream Connect Proxy")
def send_slack_message(
        external_user_id: str = Query(..., description="External user ID, e.g. abc-123"),
        account_id: str = Query(..., description="Connected Slack account ID, e.g. apn_1234567"),
        text: str = Query(..., description="The message text to send"),
        channel: str = Query(..., description="Slack channel ID, e.g. C03NA8B4VA9")
):
    # # The Slack API endpoint to send messages.
    # slack_api_url = "https://slack.com/api/chat.postMessage"
    # encoded_url = encode_url(slack_api_url)
    #
    # # Build the proxy URL for the Pipedream Connect proxy
    # proxy_url = (
    #     f"{BASE_URL}/connect/{PIPEDREAM_PROJECT_ID}/proxy/{encoded_url}"
    #     f"?external_user_id={external_user_id}&account_id={account_id}"
    # )
    #
    # # First, obtain an OAuth access token using client credentials.
    # token_url = f"{BASE_URL}/oauth/token"
    # token_payload = {
    #     "grant_type": "client_credentials",
    #     "client_id": CLIENT_ID,
    #     "client_secret": CLIENT_SECRET
    # }
    # token_response = requests.post(token_url, json=token_payload)
    # if token_response.status_code != 200:
    #     raise HTTPException(
    #         status_code=token_response.status_code,
    #         detail=f"Error generating OAuth token: {token_response.text}"
    #     )
    # access_token = token_response.json().get("access_token")
    # if not access_token:
    #     raise HTTPException(status_code=500, detail="No access token received")
    #
    # headers = {
    #     "Authorization": f"Bearer {access_token}",
    #     "x-pd-environment": PIPEDREAM_PROJECT_ENVIRONMENT,
    #     "Content-Type": "application/json"
    # }
    #
    # # Slack message payload
    # payload = {
    #     "text": text,
    #     "channel": channel
    # }
    #
    # # Send the message using the Pipedream proxy
    # response = requests.post(proxy_url, json=payload, headers=headers)
    # if response.status_code != 200:
    #     raise HTTPException(status_code=response.status_code, detail=response.text)
    #
    # return JSONResponse(response.json())
    pass

# not working ...
@app.get("/deployed-triggers", summary="List all deployed triggers for a given user")
def list_deployed_triggers(
        external_user_id: str = Query(...,
                                      description="The external user ID in your system on behalf of which you want to deploy the trigger.")
):
    """
    List all deployed triggers for a given user.
    """
    params = {"external_user_id": external_user_id}
    endpoint = f"/connect/{PIPEDREAM_PROJECT_ID}/deployed-triggers"
    return proxy_get(endpoint, params=params, environment="development")

@app.get("/deployed-triggers/{deployed_component_id}/webhooks",summary="Retrieve webhooks listening to a deployed trigger")
def retrieve_webhooks(
            deployed_component_id: str = Path(...,
                                              description="The deployed component ID for the trigger you’d like to retrieve."),
            external_user_id: str = Query(None, description="Filter by external user ID")
    ):
        """
        Retrieve the list of webhook URLs listening to a deployed trigger.
        """
        params = {}
        if external_user_id:
            params["external_user_id"] = external_user_id

        endpoint = f"/connect/{PIPEDREAM_PROJECT_ID}/deployed-triggers/{deployed_component_id}/webhooks/"
        return proxy_get(endpoint, params=params, environment="development")

@app.post("/create-webhook", summary="Create a webhook and subscribe it to an emitter")
def create_webhook(
        url: str = Query(..., description="The endpoint to which you’d like to deliver events."),
        name: str = Query(..., description="A name to assign to the webhook."),
        description: str = Query(..., description="A longer description for the webhook.")
):
    """
    Creates a webhook by calling the POST /webhooks endpoint and then creates a subscription
    to deliver events from an emitter (hardcoded emitter ID) to this webhook.

    Steps:
      1. Create the webhook using the provided URL, name, and description.
      2. Extract the webhook ID from the response.
      3. Create a subscription using the emitter_id (from your event source) and the webhook ID.
    """
    # Create the webhook
    webhook_response = requests.post(
        f"{BASE_URL}/webhooks",
        params={
            "url": url,
            "name": name,
            "description": description
        },
        headers={
            "Authorization": f"Bearer {OAUTH_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    if webhook_response.status_code != 200:
        raise HTTPException(status_code=webhook_response.status_code, detail=webhook_response.text)

    webhook_data = webhook_response.json()
    listener_id = webhook_data.get("data",{}).get("id")
    if not listener_id:
        raise HTTPException(status_code=500, detail="Webhook creation did not return an ID")

    # Hardcode the emitter_id from your event source (e.g., from https://pipedream.com/sources/dc_76u1QxA)
    EMITTER_ID = "dc_76u1QxA"

    # Create the subscription
    subscription_response = requests.post(
        f"{BASE_URL}/subscriptions",
        params={
            "emitter_id": EMITTER_ID,
            "listener_id": listener_id
        },
        headers={
            "Authorization": f"Bearer {OAUTH_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    if subscription_response.status_code != 200:
        raise HTTPException(status_code=subscription_response.status_code, detail=subscription_response.text)

    subscription_data = subscription_response.json()

    return JSONResponse({
        "webhook": webhook_data,
        "subscription": subscription_data
    })