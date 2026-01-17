from flask import render_template, url_for
from flask_login import login_required, current_user
from app.calendar import bp
from app.models import Task

@bp.route('/calendar')
@login_required
def calendar():
    tasks = Task.query.filter(Task.user_id == current_user.id, Task.planned_start != None).all()
    events = []
    for task in tasks:
        events.append({
            'title': task.title,
            'start': task.planned_start.isoformat(),
            'end': task.planned_end.isoformat() if task.planned_end else None,
            'url': url_for('tasks.edit_task', task_id=task.id)
        })
    return render_template('calendar/calendar.html', events=events)
