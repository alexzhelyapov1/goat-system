from flask import request
import httpx
from config import API_BASE_URL
from typing import Optional

def make_api_request(
    method: str,
    endpoint: str,
    json_data: Optional[dict] = None,
    form_data: Optional[dict] = None,
    params: Optional[dict] = None
):
    if json_data and form_data:
        raise ValueError("Cannot provide both json_data and form_data.")

    headers = {}
    # Check if we are in a request context and get token from cookie
    if request and hasattr(request, 'cookies'):
        token = request.cookies.get('access_token')
        if token:
            headers['Authorization'] = f'Bearer {token}'

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