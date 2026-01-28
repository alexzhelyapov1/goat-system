from flask import render_template, redirect, url_for, flash, request, jsonify, Response, session
import json
from flask_login import login_required, current_user
from app.tasks import bp
from app.services.task_service import TaskService
from app.schemas import TaskCreate, TaskSchema
from pydantic import ValidationError, TypeAdapter
from app.models import TaskStatus, TaskType, Task
from datetime import datetime
import httpx
from typing import List
from app.extensions import SessionLocal # Import SessionLocal for direct DB session


API_BASE_URL = "http://api:5001"

async def _make_api_request(method: str, endpoint: str, task_id: int = None, json_data: dict = None, params: dict = None):
    headers = {}
    if 'jwt_token' in session:
        headers["Authorization"] = f"Bearer {session['jwt_token']}"

    url = f"{API_BASE_URL}{endpoint}"
    if task_id:
        url = f"{url}{task_id}"

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

@bp.route('/tasks')
@login_required
async def tasks():
    task_type = request.args.get('type', 'all')
    try:
        response = await _make_api_request("GET", "/tasks/", params={'type': task_type})
        tasks_data = response.json()
        tasks = TypeAdapter(List[TaskSchema]).validate_python(tasks_data)
    except httpx.RequestError:
        tasks = []
    return render_template('tasks/tasks_list.html', tasks=tasks, current_filter=task_type, task_statuses=TaskStatus, task_types=TaskType)

@bp.route('/task/<int:task_id>/json')
@login_required
async def task_json(task_id):
    try:
        response = await _make_api_request("GET", f"/tasks/{task_id}")
        return jsonify(response.json())
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
async def create_task():
    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()
            for key in ['deadline', 'planned_start', 'planned_end', 'suspend_due', 'notify_at']:
                date_val = form_data.get(f'{key}_date')
                time_val = form_data.get(f'{key}_time')

                if date_val:
                    if not time_val:
                        time_val = '00:00'
                    form_data[key] = f'{date_val}T{time_val}:00' # Assuming seconds are 00
                else:
                    form_data[key] = None
            
            if not form_data.get('duration'):
                form_data['duration'] = None
            else:
                form_data['duration'] = int(form_data['duration'])

            if form_data.get('planned_start'):
                form_data['type'] = 'CALENDAR'

            # a crutch to remove empty values
            task_data = {k: v for k, v in form_data.items() if v is not None}

            await _make_api_request("POST", "/tasks/", json_data=task_data)
            flash('Task created successfully!')
            return redirect(request.referrer or url_for('tasks.tasks'))
        except (ValidationError, httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            flash(str(e))
            return redirect(url_for('tasks.create_task'))
    return render_template('tasks/task_form.html', form_title='Create Task', task_statuses=TaskStatus, task_types=TaskType)

@bp.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
async def edit_task(task_id):
    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()
            for key in ['deadline', 'planned_start', 'planned_end', 'suspend_due', 'notify_at']:
                date_val = form_data.get(f'{key}_date')
                time_val = form_data.get(f'{key}_time')

                if date_val:
                    if not time_val:
                        time_val = '00:00'
                    form_data[key] = f'{date_val}T{time_val}:00'
                else:
                    form_data[key] = None
            
            if not form_data.get('duration'):
                form_data['duration'] = None
            else:
                form_data['duration'] = int(form_data['duration'])

            if form_data.get('planned_start'):
                form_data['type'] = 'CALENDAR'

            task_data = {k: v for k, v in form_data.items() if v is not None}

            await _make_api_request("PUT", f"/tasks/{task_id}", json_data=task_data)
            flash('Task updated successfully!')
            return redirect(request.referrer or url_for('tasks.tasks'))
        except (ValidationError, httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            flash(str(e))
    
    try:
        response = await _make_api_request("GET", f"/tasks/{task_id}")
        task = response.json()
    except httpx.RequestError as e:
        flash(f"Error fetching task: {e}")
        return redirect(url_for('tasks.tasks'))

    return render_template('tasks/task_form.html', task=task, form_title='Edit Task', task_statuses=TaskStatus, task_types=TaskType)

@bp.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
async def delete_task(task_id):
    try:
        await _make_api_request("DELETE", f"/tasks/{task_id}")
        flash('Task deleted successfully!')
        return jsonify({'success': True})
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/tasks/export')
@login_required
def export_tasks():
    fields = request.args.getlist('fields')
    # This still uses the service directly, as it's a specific feature.
    # This can be migrated later.
    tasks = TaskService.get_all_tasks_for_user(current_user.id)

    tasks_to_export = []
    for task in tasks:
        task_dict = TaskSchema.model_validate(task).model_dump(mode="json")
        exported_task = {field: task_dict.get(field) for field in fields}
        tasks_to_export.append(exported_task)

    response_data = json.dumps(tasks_to_export, ensure_ascii=False, indent=4)
    response = Response(response_data, mimetype='application/json; charset=utf-8')
    response.headers['Content-Disposition'] = 'attachment; filename=tasks.json'
    return response

@bp.route('/tasks/import', methods=['POST'])
@login_required
def import_tasks():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('tasks.tasks'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('tasks.tasks'))
    if file:
        try:
            tasks_data = json.load(file)
            for task_data in tasks_data:
                task_data.pop('id', None)
                # This still uses the service directly.
                # This can be migrated later.
                task = TaskCreate(**task_data)
                TaskService.create_task(task, current_user.id)
            flash('Tasks imported successfully!')
        except (json.JSONDecodeError, ValidationError) as e:
            flash(f'Error importing tasks: {e}')
        return redirect(url_for('tasks.tasks'))

@bp.route('/task/<int:task_id>')
@login_required
async def task(task_id):
    try:
        response = await _make_api_request("GET", f"/tasks/{task_id}")
        task_data = response.json()
        task = TypeAdapter(TaskSchema).validate_python(task_data)
        if task.user_id != current_user.id:
            flash('You are not authorized to view this task.')
            return redirect(url_for('tasks.tasks'))
        return render_template('tasks/task_form.html', task=task, form_title='Edit Task', task_statuses=TaskStatus, task_types=TaskType)
    except httpx.RequestError as e:
        flash(f"Error fetching task: {e}")
        return redirect(url_for('tasks.tasks'))