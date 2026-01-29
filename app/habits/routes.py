from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required
from app.habits import bp
from app.schemas import HabitSchema
from pydantic import ValidationError, TypeAdapter
from datetime import date, timedelta, datetime
import httpx
import json
from typing import List
from app.api_client import make_api_request


@bp.route('/habits')
@login_required
def habits():
    try:
        response = make_api_request("GET", "/habits/")
        habits_data = response.json()
        habits = TypeAdapter(List[HabitSchema]).validate_python(habits_data)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Could not load habits: {e}", "danger")
        habits = []
        
    habits.sort(key=lambda x: x.strategy_type)
    
    today = date.today()
    start_date = today - timedelta(days=3)
    end_date = today + timedelta(days=3)
    
    habits_with_logs = []
    for habit in habits:
        try:
            params = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
            response = make_api_request("GET", f"/habits/{habit.id}/dates-with-status", params=params)
            dates_with_status_raw = response.json()
            # Convert string keys back to date objects
            dates_with_status = {date.fromisoformat(k): v for k, v in dates_with_status_raw.items()}
            
            habits_with_logs.append({
                "habit": habit,
                "logs": dates_with_status
            })
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            flash(f"Could not load logs for habit '{habit.name}': {e}", "warning")
            habits_with_logs.append({"habit": habit, "logs": {}})


    return render_template('habits/habits_list.html', habits_with_logs=habits_with_logs, dates=[start_date + timedelta(days=i) for i in range(7)], today=today)

@bp.route('/habit/<int:habit_id>/json')
@login_required
def habit_json(habit_id):
    try:
        response = make_api_request("GET", f"/habits/{habit_id}")
        return jsonify(response.json())
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return jsonify({'error': str(e)}), 500

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
                start_date = datetime.utcnow().date().isoformat()

            end_date = request.form.get('end_date')
            if not end_date:
                end_date = None

            habit_data = {
                "name": request.form['name'],
                "description": request.form.get('description'),
                "start_date": start_date,
                "end_date": end_date,
                "strategy_type": request.form['strategy_type'],
                "strategy_params": strategy_params
            }
            
            make_api_request("POST", "/habits/", json_data=habit_data)

            flash('Habit created successfully!', 'success')
            return redirect(url_for('habits.habits'))
        except (ValidationError, json.JSONDecodeError, ValueError, httpx.RequestError, httpx.HTTPStatusError) as e:
            flash(str(e), 'danger')
            return redirect(url_for('habits.create_habit'))
    return render_template('habits/habit_form.html')

@bp.route('/habits/edit/<int:habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    if request.method == 'POST':
        try:
            strategy_params_str = request.form.get('strategy_params')
            if not strategy_params_str:
                strategy_params_str = '{}'
            strategy_params = json.loads(strategy_params_str)
            
            start_date = request.form.get('start_date')
            if not start_date:
                start_date = datetime.utcnow().date().isoformat()

            end_date = request.form.get('end_date')
            if not end_date:
                end_date = None

            habit_data = {
                "name": request.form['name'],
                "description": request.form.get('description'),
                "start_date": start_date,
                "end_date": end_date,
                "strategy_type": request.form['strategy_type'],
                "strategy_params": strategy_params
            }
            
            make_api_request("PUT", f"/habits/{habit_id}", json_data=habit_data)

            flash('Habit updated successfully!', 'success')
            return redirect(url_for('habits.habits'))
        except (ValidationError, json.JSONDecodeError, ValueError, httpx.RequestError, httpx.HTTPStatusError) as e:
            flash(str(e), 'danger')
            return redirect(url_for('habits.edit_habit', habit_id=habit_id))
    
    try:
        response = make_api_request("GET", f"/habits/{habit_id}")
        habit = response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Error fetching habit: {e}", 'danger')
        return redirect(url_for('habits.habits'))

    return render_template('habits/habit_form.html', habit=habit)

@bp.route('/habit/delete/<int:habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    try:
        make_api_request("DELETE", f"/habits/{habit_id}")
        flash('Habit deleted successfully!', 'success')
        return jsonify({'success': True})
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/habits/log', methods=['POST'])
@login_required
def log_habit():
    try:
        log_data = {
            "habit_id": int(request.form['habit_id']),
            "date": request.form['date'],
            "is_done": request.form.get('is_done') == 'true',
            "index": int(request.form.get('index', 0))
        }
        make_api_request("POST", "/habits/log", json_data=log_data)
        return jsonify({'success': True})
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
        return jsonify({'error': str(e)}), 500