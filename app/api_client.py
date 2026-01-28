from flask import session, flash, url_for, redirect
import httpx
from config import API_BASE_URL
from typing import Optional


async def make_api_request(method: str, endpoint: str, item_id: Optional[int] = None, json_data: Optional[dict] = None, form_data: Optional[dict] = None, params: Optional[dict] = None):
    if json_data and form_data:
        raise ValueError("Cannot provide both json_data and form_data.")

    headers = {}
    if 'jwt_token' in session:
        headers["Authorization"] = f"Bearer {session['jwt_token']}"

    url = f"{API_BASE_URL}{endpoint}"
    if item_id:
        url = f"{url}{item_id}"

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await client.post(url, json=json_data, data=form_data, headers=headers, params=params)
            elif method == "PUT":
                response = await client.put(url, json=json_data, data=form_data, headers=headers, params=params)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                raise ValueError("Unsupported HTTP method")

            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                flash("Your session has expired. Please log in again.")
                # For now, we redirect to login on 401. A more robust solution might use a global
                # Flask before_request or client-side handling to catch all 401s.
                # return redirect(url_for('auth.login')) # Cannot redirect from here directly
            elif e.response.status_code == 403:
                flash("You are not authorized to perform this action.")
            else:
                flash(f"API Error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            flash(f"Network Error: Could not connect to API - {e}")
            raise