from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from fastapi.responses import JSONResponse
from app.config import PIPEDREAM_API_HOST, OAUTH_TOKEN, PIPEDREAM_PROJECT_ID, PIPEDREAM_PROJECT_ENVIRONMENT, CLIENT_ID, CLIENT_SECRET, BASE_URL
from app.helpers import proxy_get
import requests

routes = APIRouter(tags=["Webhooks"])

# not working ...
@routes.get("/deployed-triggers", summary="List all deployed triggers for a given user")
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

@routes.get("/deployed-triggers/{deployed_component_id}/webhooks",summary="Retrieve webhooks listening to a deployed trigger")
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

@routes.post("/create-webhook", summary="Create a webhook and subscribe it to an emitter")
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