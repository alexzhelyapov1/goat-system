from flask import render_template, redirect, url_for, flash, request, jsonify, Response
import json
from flask_login import login_required, current_user
from app.tasks import bp
from app.services.task_service import TaskService
from app.schemas import TaskCreate, TaskSchema
from pydantic import ValidationError
from app.models import TaskStatus, TaskType, Task
from datetime import datetime

@bp.route('/tasks')
@login_required
def tasks():
    task_type = request.args.get('type', 'all')
    tasks = TaskService.get_tasks_by_user_and_type(current_user.id, task_type)
    return render_template('tasks/tasks_list.html', tasks=tasks, current_filter=task_type, task_statuses=TaskStatus, task_types=TaskType)

@bp.route('/task/<int:task_id>')
@login_required
def task(task_id):
    task = TaskService.get_task(task_id)
    if task.user_id != current_user.id:
        flash('You are not authorized to view this task.')
        return redirect(url_for('tasks.tasks'))
    return render_template('tasks/task_form.html', task=task, form_title='Edit Task', task_statuses=TaskStatus, task_types=TaskType)

@bp.route('/task/<int:task_id>/json')
@login_required
def task_json(task_id):
    task = TaskService.get_task(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(TaskSchema.model_validate(task).model_dump(mode="json"))

@bp.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()
            for key in ['deadline', 'planned_start', 'planned_end', 'suspend_due', 'notify_at']:
                date_val = form_data.get(f'{key}_date')
                time_val = form_data.get(f'{key}_time')

                if date_val:
                    if not time_val:
                        time_val = '00:00'
                    form_data[key] = f'{date_val}T{time_val}+03:00'
                else:
                    form_data[key] = None

            if not form_data.get('duration'):
                form_data['duration'] = None

            if form_data.get('planned_start'):
                form_data['type'] = 'CALENDAR'
            task_data = TaskCreate(**form_data)
            TaskService.create_task(task_data, current_user.id)
            flash('Task created successfully!')
            return redirect(request.referrer or url_for('tasks.tasks'))
        except ValidationError as e:
            flash(str(e.errors()))
            return redirect(url_for('tasks.create_task'))
    return render_template('tasks/task_form.html', form_title='Create Task', task_statuses=TaskStatus, task_types=TaskType)

@bp.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = TaskService.get_task(task_id)
    if task.user_id != current_user.id:
        flash('You are not authorized to edit this task.')
        return redirect(url_for('tasks.tasks'))
    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()
            for key in ['deadline', 'planned_start', 'planned_end', 'suspend_due', 'notify_at']:
                date_val = form_data.get(f'{key}_date')
                time_val = form_data.get(f'{key}_time')

                if date_val:
                    if not time_val:
                        time_val = '00:00'
                    form_data[key] = f'{date_val}T{time_val}+03:00'
                else:
                    form_data[key] = None

            if not form_data.get('duration'):
                form_data['duration'] = None

            if form_data.get('planned_start'):
                form_data['type'] = 'CALENDAR'
            task_data = TaskCreate(**form_data)
            TaskService.update_task(task_id, task_data)
            flash('Task updated successfully!')
            return redirect(request.referrer or url_for('tasks.tasks'))
        except ValidationError as e:
            flash(str(e.errors()))
    return render_template('tasks/task_form.html', task=task, form_title='Edit Task', task_statuses=TaskStatus, task_types=TaskType)

@bp.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = TaskService.get_task(task_id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    TaskService.delete_task(task_id)
    flash('Task deleted successfully!')
    return jsonify({'success': True})

@bp.route('/tasks/export')
@login_required
def export_tasks():
    fields = request.args.getlist('fields')
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
                task = TaskCreate(**task_data)
                TaskService.create_task(task, current_user.id)
            flash('Tasks imported successfully!')
        except (json.JSONDecodeError, ValidationError) as e:
            flash(f'Error importing tasks: {e}')
        return redirect(url_for('tasks.tasks'))
