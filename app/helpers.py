import base64
import requests
from fastapi import HTTPException
from app.config import OAUTH_TOKEN, BASE_URL
def encode_url(url: str) -> str:
    """
    URL safe Base64 encode the given URL.
    """
    encoded_bytes = base64.urlsafe_b64encode(url.encode())
    return encoded_bytes.decode().rstrip("=")



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
