import uuid
import requests
from fastapi import FastAPI, HTTPException, Query, Request, Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.routers.accounts_routes import routes as account_routes
from app.routers.webhooks import routes as webhook_routes
from app.tools.gitlab import routes as gitlab_routes
from app.tools.slack import routes as slack_routes

from app.config import PIPEDREAM_API_HOST, OAUTH_TOKEN, PIPEDREAM_PROJECT_ID, PIPEDREAM_PROJECT_ENVIRONMENT, CLIENT_ID, CLIENT_SECRET, BASE_URL
from app.helpers import encode_url, proxy_get

app = FastAPI(title="Pipedream REST API Proxy")
templates = Jinja2Templates(directory="templates")
app.include_router(account_routes)
app.include_router(webhook_routes)

app.include_router(gitlab_routes)
app.include_router(slack_routes)

@app.post("/webhook", response_class=HTMLResponse)
async def webhook(request: Request):
    print("--------------------------webhook got the trigger action--------------------------")
    x  = await request.json()
    print(x)
    return JSONResponse({"message": "Webhook triggered successfully!"})

@app.get("/", response_class=HTMLResponse)
@app.get("/connect/{auth_type}", response_class=HTMLResponse)
async def connection_auth(request: Request,auth_type: str = None,oauth_client_id: str = Query(None, description="OAuth Custom Client ID")):
    """
    Render the authentication page.
    """
    if auth_type is None:
        auth_type = "notion"
    return templates.TemplateResponse("connection.html", {"request": request, "oauthClientId": oauth_client_id,"auth_type": auth_type})

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

@app.get("/connect/{project_id}/actions/{app}")
def get_project_actions(
        project_id: str,
        app: str = Path(..., description="App name, e.g. gitlab", example="gitlab", placeholder="gitlab")
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
        "conversation": {
            "__lv": {
                "label": "Public channel: test-user",
                "value": "C0772SYKNN4"
            }    
        },
        # "channel": "#test-user",
        "thread_broadcast": False,#
        "unfurl_links": False,#
        "unfurl_media": False,#
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
