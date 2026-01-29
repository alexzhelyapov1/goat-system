from flask import session
import httpx
from config import API_BASE_URL
from typing import Optional

async def make_api_request(
    method: str, 
    endpoint: str, 
    json_data: Optional[dict] = None, 
    form_data: Optional[dict] = None, 
    params: Optional[dict] = None
):
    if json_data and form_data:
        raise ValueError("Cannot provide both json_data and form_data.")

    headers = {}
    if 'jwt_token' in session:
        headers["Authorization"] = f"Bearer {session['jwt_token']}"

    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method == "POST":
            response = await client.post(url, json=json_data, data=form_data, headers=headers, params=params)
        elif method == "PUT":
            response = await client.put(url, json=json_data, data=form_data, headers=headers, params=params)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response