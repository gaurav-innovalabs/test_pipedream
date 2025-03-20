
from fastapi import APIRouter, HTTPException, Query, Path
from app.config import PIPEDREAM_API_HOST, OAUTH_TOKEN, PIPEDREAM_PROJECT_ID, PIPEDREAM_PROJECT_ENVIRONMENT, CLIENT_ID, CLIENT_SECRET, BASE_URL
from app.helpers import encode_url
import requests

routes = APIRouter(tags=["GitLab"])

@routes.post("/connect/{project_id}/components/{action_name}/run/gitlab")
def execute_gitlab(
        project_id: str,
):
    """
    Execute a specific action for a user.
    """
    url = f"{BASE_URL}/connect/{project_id}/actions/run"
    payload = {
        "external_user_id": "xyz",
        "id": "gitlab-list-repo-branches",
        "configured_props": {
            "gitlab": {
                "authProvisionId": "apn_AVh5D0v"
            },
            "projectId": "68209297"
        }
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

@routes.post("/connect/{project_id}/components/{action_name}/run/notion")
def execute_notion(
        project_id: str,
):
    """
    Execute a specific action for a user.
    """
    url = f"{BASE_URL}/connect/{project_id}/actions/run"
    payload = {
        "external_user_id": "e7a1120c-0aed-4aa3-b9d7-c335dca356c7",
        "id": "notion-search",
        "configured_props": {
            "notion": {
                "authProvisionId": "apn_Dph5vrn"
            },
            "title": "PrioHire",
            # "filter": "page",
            # "sortDirection": "ascending",
            # "pageSize": 100
        }
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

@routes.post("/proxy/{project_id}/send-gitlab", summary="Send a GitLab request via Pipedream Connect Proxy")
def send_gitlab_request(
        project_id: str = Path(..., description="Project ID, e.g. proj_W7srqA0"),
        external_user_id: str = Query(..., description="External user ID, e.g. xyz"),
        account_id: str = Query(..., description="Connected GitLab account ID, e.g. apn_AVh5D0v"),
        gitlab_project_id: int = Query(..., description="GitLab project ID, e.g. 68209297")
):
    # The GitLab API endpoint to list branches
    gitlab_api_url = f"https://gitlab.com/api/v4/projects/{gitlab_project_id}/repository/branches"
    encoded_url = encode_url(gitlab_api_url)
    
    url = f"{BASE_URL}/connect/{project_id}/proxy/{encoded_url}"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OAUTH_TOKEN}",
        "X-PD-Environment": "development"
    }
    
    params = {
        "external_user_id": external_user_id,
        "account_id": account_id
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
