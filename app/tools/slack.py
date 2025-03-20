
from fastapi import APIRouter, HTTPException, Query, Path
from app.config import PIPEDREAM_API_HOST, OAUTH_TOKEN, PIPEDREAM_PROJECT_ID, PIPEDREAM_PROJECT_ENVIRONMENT, CLIENT_ID, CLIENT_SECRET, BASE_URL
import requests

routes = APIRouter(tags=["Slack"])
@routes.post("/connect/{project_id}/components/{action_name}/run/slack/list-channels")
def list_channels(
        project_id: str,
        external_user_id: str = Query(..., description="External user ID, e.g. abc-123",placeholder="31b294c4-450f-446c-ad4d-c49178f577de"),
        apn_key: str = Query(..., description="Connected Slack account ID, e.g. apn_gyhGpEj",placeholder="apn_gyhGpEj")
):
    """
    Execute a specific action for a user.
    """
    url = f"{BASE_URL}/connect/{project_id}/actions/run"
    payload = {
        "external_user_id": external_user_id,
        "id": "slack-list-channels",
        "configured_props": {
            "slack": {
                "authProvisionId": apn_key
            },
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

@routes.post("/connect/{project_id}/components/{action_name}/run/slack/send_message")
def send_message(
        project_id: str,
        external_user_id: str = Query(..., description="External user ID, e.g. abc-123",placeholder="31b294c4-450f-446c-ad4d-c49178f577de"),
        apn_key: str = Query(..., description="Connected Slack account ID, e.g. apn_gyhGpEj",placeholder="apn_gyhGpEj")
):
    """
    Execute a specific action for a user.
    """
    url = f"{BASE_URL}/connect/{project_id}/actions/run"
    payload = {
        "external_user_id": external_user_id,
        "id": "slack-send-message",
        "configured_props": {
            "slack": {
                "authProvisionId": apn_key
            },
            "channelType": "channel",
            "conversation": "C0772SYKNN4",
            "text": "hi",
            "mrkdwn": True,
            "as_user": False,
            "post_at": None,
            "include_sent_via_pipedream_flag": True,
            "customizeBotSettings": False,
            "replyToThread": False,
            "addMessageMetadata": False,
            "configureUnfurlSettings": False
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