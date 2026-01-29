from flask import render_template, url_for, flash
from flask_login import login_required
from app.calendar import bp
from app.schemas import TaskSchema
from pydantic import TypeAdapter
import httpx
from typing import List
from app.api_client import make_api_request

@bp.route('/calendar')
@login_required
def calendar():
    try:
        response = make_api_request("GET", "/tasks/calendar")
        tasks_data = response.json()
        tasks = TypeAdapter(List[TaskSchema]).validate_python(tasks_data)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Error loading calendar data: {e}", "danger")
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
