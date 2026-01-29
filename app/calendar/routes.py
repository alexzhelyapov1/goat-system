from flask import render_template, url_for, flash, session
from flask_login import login_required, current_user
from app.calendar import bp
from app.schemas import TaskSchema
from pydantic import TypeAdapter
import httpx
from typing import List


API_BASE_URL = "http://api:5001"

async def _make_api_request(method: str, endpoint: str, json_data: dict = None, params: dict = None):
    headers = {}
    if 'jwt_token' in session:
        headers["Authorization"] = f"Bearer {session['jwt_token']}"

    url = f"{API_BASE_URL}{endpoint}"

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await client.post(url, json=json_data, headers=headers, params=params)
            elif method == "PUT":
                response = await client.put(url, json=json_data, headers=headers, params=params)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                raise ValueError("Unsupported HTTP method")

            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                flash("Your session has expired. Please log in again.")
                # Redirect to login page, this should be handled by client-side or
                # a global Flask before_request if all API calls need auth
            elif e.response.status_code == 403:
                flash("You are not authorized to perform this action.")
            else:
                flash(f"API Error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            flash(f"Network Error: Could not connect to API - {e}")
            raise

@bp.route('/calendar')
@login_required
async def calendar():
    try:
        response = await _make_api_request("GET", "/tasks/calendar")
        tasks_data = response.json()
        tasks = TypeAdapter(List[TaskSchema]).validate_python(tasks_data)
    except httpx.RequestError:
        tasks = []
    
    events = []
    for task in tasks:
        events.append({
            'title': task.title,
            'start': task.planned_start.isoformat(),
            'end': task.planned_end.isoformat() if task.planned_end else None,
            'url': url_for('tasks.edit_task', task_id=task.id)
        })
    return render_template('calendar/calendar.html', events=events)
