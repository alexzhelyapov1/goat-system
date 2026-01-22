from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.habits import bp
from app.services.habit_service import HabitService
from app.schemas import HabitCreate, HabitSchema
from pydantic import ValidationError
from datetime import date, timedelta, datetime
import json

@bp.route('/habits')
@login_required
def habits():
    habits = HabitService.get_habits_by_user(current_user.id)
    habits.sort(key=lambda x: x.strategy_type)
    
    today = date.today()
    start_date = today - timedelta(days=3)
    end_date = today + timedelta(days=3)
    
    habits_with_logs = []
    for habit in habits:
        dates_with_status = HabitService.get_habit_dates_with_status(habit.id, start_date, end_date)
        habits_with_logs.append({
            "habit": habit,
            "logs": dates_with_status
        })

    return render_template('habits/habits_list.html', habits_with_logs=habits_with_logs, dates=[start_date + timedelta(days=i) for i in range(7)], today=today)

@bp.route('/habit/<int:habit_id>/json')
@login_required
def habit_json(habit_id):
    habit = HabitService.get_habit(habit_id)
    if habit.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(HabitSchema.from_orm(habit).model_dump(mode='json'))

@bp.route('/habits/create', methods=['GET', 'POST'])
@login_required
def create_habit():
    if request.method == 'POST':
        try:
            strategy_params_str = request.form.get('strategy_params')
            if not strategy_params_str:
                strategy_params_str = '{}'
            strategy_params = json.loads(strategy_params_str)

            start_date = request.form.get('start_date')
            if not start_date:
                start_date = datetime.utcnow().date()

            end_date = request.form.get('end_date')
            if not end_date:
                end_date = None

            habit_data = HabitCreate(
                name=request.form['name'],
                description=request.form.get('description'),
                start_date=start_date,
                end_date=end_date,
                strategy_type=request.form['strategy_type'],
                strategy_params=strategy_params
            )
            HabitService.create_habit(habit_data, current_user.id)
            flash('Habit created successfully!')
            return redirect(url_for('habits.habits'))
        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            flash(str(e))
            return redirect(url_for('habits.create_habit'))
    return render_template('habits/habit_form.html')

@bp.route('/habits/edit/<int:habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    habit = HabitService.get_habit(habit_id)
    if habit.user_id != current_user.id:
        flash('You are not authorized to edit this habit.')
        return redirect(url_for('habits.habits'))
    if request.method == 'POST':
        try:
            strategy_params_str = request.form.get('strategy_params')
            if not strategy_params_str:
                strategy_params_str = '{}'
            strategy_params = json.loads(strategy_params_str)
            
            start_date = request.form.get('start_date')
            if not start_date:
                start_date = datetime.utcnow().date()

            end_date = request.form.get('end_date')
            if not end_date:
                end_date = None

            habit_data = HabitCreate(
                name=request.form['name'],
                description=request.form.get('description'),
                start_date=start_date,
                end_date=end_date,
                strategy_type=request.form['strategy_type'],
                strategy_params=strategy_params
            )
            HabitService.update_habit(habit_id, habit_data)
            flash('Habit updated successfully!')
            return redirect(url_for('habits.habits'))
        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            flash(str(e))
            return redirect(url_for('habits.edit_habit', habit_id=habit_id))
    return render_template('habits/habit_form.html', habit=habit)

@bp.route('/habit/delete/<int:habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    habit = HabitService.get_habit(habit_id)
    if habit.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    HabitService.delete_habit(habit_id)
    flash('Habit deleted successfully!')
    return jsonify({'success': True})

@bp.route('/habits/log', methods=['POST'])
@login_required
def log_habit():
    habit_id = request.form['habit_id']
    habit = HabitService.get_habit(habit_id)
    if habit.user_id != current_user.id:
        flash('You are not authorized to log this habit.')
        return redirect(url_for('habits.habits'))
    log_date_str = request.form['date']
    is_done = request.form.get('is_done') == 'true'
    log_date = date.fromisoformat(log_date_str)
    index = request.form.get('index', 0, type=int)
    
    HabitService.log_habit(habit_id, log_date, is_done, index)
    
    return redirect(url_for('habits.habits'))
