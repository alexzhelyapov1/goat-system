from flask import render_template, redirect, url_for, flash, request, jsonify, Response
import json
from flask_login import login_required, current_user
from app.tasks import bp
from app.services.task_service import TaskService
from app.schemas import TaskCreate, TaskSchema
from pydantic import ValidationError
from app.models import TaskStatus, TaskType, Task
from datetime import datetime
from app.extensions import db

@bp.route('/tasks')
@login_required
def tasks():
    return render_template('tasks/tasks_list.html')

@bp.route('/tasks/export')
@login_required
def export_tasks():
    task_service = TaskService(db_session=db.session)
    fields = request.args.getlist('fields')
    tasks = task_service.get_all_tasks_for_user(current_user.id)

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
    task_service = TaskService(db_session=db.session)
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
                task_service.create_task(task, current_user.id)
            flash('Tasks imported successfully!')
        except (json.JSONDecodeError, ValidationError) as e:
            flash(f'Error importing tasks: {e}')
        return redirect(url_for('tasks.tasks'))
