from flask import render_template, redirect, url_for, flash, request, jsonify, Response, session
import json
from flask_login import login_required
from app.tasks import bp
from app.schemas import TaskSchema
from pydantic import ValidationError, TypeAdapter
from app.models import TaskStatus, TaskType
from datetime import datetime
import httpx
from typing import List
from app.api_client import make_api_request


@bp.route('/tasks')
@login_required
async def tasks():
    task_type = request.args.get('type', 'all')
    try:
        response = await make_api_request("GET", "/tasks/", params={'type': task_type})
        tasks_data = response.json()
        tasks = TypeAdapter(List[TaskSchema]).validate_python(tasks_data)
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        flash(f"Could not load tasks: {e}", "danger")
        tasks = []
    return render_template('tasks/tasks_list.html', tasks=tasks, current_filter=task_type, task_statuses=TaskStatus, task_types=TaskType)

@bp.route('/task/<int:task_id>/json')
@login_required
async def task_json(task_id):
    try:
        response = await make_api_request("GET", f"/tasks/{task_id}")
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

            task_data = {k: v for k, v in form_data.items() if v is not None}

            await make_api_request("POST", "/tasks/", json_data=task_data)
            flash('Task created successfully!', 'success')
            return redirect(request.referrer or url_for('tasks.tasks'))
        except (ValidationError, httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            flash(str(e), 'danger')
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

            await make_api_request("PUT", f"/tasks/{task_id}", json_data=task_data)
            flash('Task updated successfully!', 'success')
            return redirect(request.referrer or url_for('tasks.tasks'))
        except (ValidationError, httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
            flash(str(e), 'danger')
    
    try:
        response = await make_api_request("GET", f"/tasks/{task_id}")
        task = response.json()
        
        # Convert date strings back to datetime objects for the template
        for key in ['deadline', 'planned_start', 'planned_end', 'suspend_due', 'notify_at']:
            if key in task and task[key] and isinstance(task[key], str):
                task[key] = datetime.fromisoformat(task[key])

    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Error fetching task: {e}", 'danger')
        return redirect(url_for('tasks.tasks'))

    return render_template('tasks/task_form.html', task=task, form_title='Edit Task', task_statuses=TaskStatus, task_types=TaskType)

@bp.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
async def delete_task(task_id):
    try:
        await make_api_request("DELETE", f"/tasks/{task_id}")
        flash('Task deleted successfully!', 'success')
        return jsonify({'success': True})
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Error deleting task: {e}", 'danger')
        return jsonify({'error': str(e)}), 500

@bp.route('/tasks/export')
@login_required
async def export_tasks():
    fields = request.args.getlist('fields')
    try:
        response = await make_api_request("GET", "/tasks/export", params={'fields': fields})
        tasks_to_export = response.json()
        
        response_data = json.dumps(tasks_to_export, ensure_ascii=False, indent=4)
        response = Response(response_data, mimetype='application/json; charset=utf-8')
        response.headers['Content-Disposition'] = 'attachment; filename=tasks.json'
        return response
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Error exporting tasks: {e}", 'danger')
        return redirect(url_for('tasks.tasks'))

@bp.route('/tasks/import', methods=['POST'])
@login_required
async def import_tasks():
    if 'file' not in request.files:
        flash('No file part', 'warning')
        return redirect(url_for('tasks.tasks'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for('tasks.tasks'))
    if file:
        try:
            tasks_data = json.load(file)
            await make_api_request("POST", "/tasks/import", json_data=tasks_data)
            flash('Tasks imported successfully!', 'success')
        except (json.JSONDecodeError, httpx.RequestError, httpx.HTTPStatusError) as e:
            flash(f'Error importing tasks: {e}', 'danger')
        return redirect(url_for('tasks.tasks'))

@bp.route('/task/<int:task_id>')
@login_required
async def task(task_id):
    try:
        response = await make_api_request("GET", f"/tasks/{task_id}")
        task_data = response.json()
        # The API is the source of truth, no need to check user_id here
        task = TypeAdapter(TaskSchema).validate_python(task_data)
        return render_template('tasks/task_form.html', task=task, form_title='Edit Task', task_statuses=TaskStatus, task_types=TaskType)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Error fetching task: {e}", 'danger')
        return redirect(url_for('tasks.tasks'))