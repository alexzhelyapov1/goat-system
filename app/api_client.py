from flask import request
import httpx
from config import API_BASE_URL
from typing import Optional

def make_api_request(
    method: str,
    endpoint: str,
    json_data: Optional[dict] = None,
    form_data: Optional[dict] = None,
    params: Optional[dict] = None,
    token: Optional[str] = None
):
    if json_data and form_data:
        raise ValueError("Cannot provide both json_data and form_data.")

    headers = {}
    auth_token = token
    # If no token is provided as an argument, try to get it from the cookie
    if not auth_token and request and hasattr(request, 'cookies'):
        auth_token = request.cookies.get('access_token')

    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'

    url = f"{API_BASE_URL}{endpoint}"

    with httpx.Client() as client:
        if method == "GET":
            response = client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = client.post(url, json=json_data, data=form_data, headers=headers, params=params)
        elif method == "PUT":
            response = client.put(url, json=json_data, data=form_data, headers=headers, params=params)
        elif method == "DELETE":
            response = client.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response