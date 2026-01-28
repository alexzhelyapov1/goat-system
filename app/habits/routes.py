from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required
from app.habits import bp
from app.schemas import HabitSchema
from pydantic import TypeAdapter
from datetime import date, timedelta, datetime
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
                response = await client.post(url, json=json_data, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=json_data, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
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


@bp.route('/habits')
@login_required
async def habits():
    try:
        response = await _make_api_request("GET", "/habits/")
        habits_data = response.json()
        habits = TypeAdapter(List[HabitSchema]).validate_python(habits_data)
    except httpx.RequestError:
        habits = []
        
    habits.sort(key=lambda x: x.strategy_type)
    
    today = date.today()
    start_date = today - timedelta(days=3)
    end_date = today + timedelta(days=3)
    
    habits_with_logs = []
    for habit in habits:
        try:
            params = {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
            response = await _make_api_request("GET", f"/habits/{habit.id}/dates-with-status", params=params)
            dates_with_status_raw = response.json()
            # Convert string keys back to date objects
            dates_with_status = {date.fromisoformat(k): v for k, v in dates_with_status_raw.items()}
            
            habits_with_logs.append({
                "habit": habit,
                "logs": dates_with_status
            })
        except httpx.RequestError:
            # If fetching logs for one habit fails, we can either skip it or show an error.
            # For now, let's just not add it to the list.
            flash(f"Could not load logs for habit '{habit.name}'.")

    return render_template('habits/habits_list.html', habits_with_logs=habits_with_logs, dates=[start_date + timedelta(days=i) for i in range(7)], today=today)

@bp.route('/habit/<int:habit_id>/json')
@login_required
async def habit_json(habit_id):
    try:
        response = await _make_api_request("GET", f"/habits/{habit_id}")
        return jsonify(response.json())
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/habits/create', methods=['GET', 'POST'])
@login_required
async def create_habit():
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
            
            await _make_api_request("POST", "/habits/", json_data=habit_data)

            flash('Habit created successfully!')
            return redirect(url_for('habits.habits'))
        except (ValidationError, json.JSONDecodeError, ValueError, httpx.RequestError, httpx.HTTPStatusError) as e:
            flash(str(e))
            return redirect(url_for('habits.create_habit'))
    return render_template('habits/habit_form.html')

@bp.route('/habits/edit/<int:habit_id>', methods=['GET', 'POST'])
@login_required
async def edit_habit(habit_id):
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
            
            await _make_api_request("PUT", f"/habits/{habit_id}", json_data=habit_data)

            flash('Habit updated successfully!')
            return redirect(url_for('habits.habits'))
        except (ValidationError, json.JSONDecodeError, ValueError, httpx.RequestError, httpx.HTTPStatusError) as e:
            flash(str(e))
            return redirect(url_for('habits.edit_habit', habit_id=habit_id))
    
    try:
        response = await _make_api_request("GET", f"/habits/{habit_id}")
        habit = response.json()
    except httpx.RequestError as e:
        flash(f"Error fetching habit: {e}")
        return redirect(url_for('habits.habits'))

    return render_template('habits/habit_form.html', habit=habit)

@bp.route('/habit/delete/<int:habit_id>', methods=['POST'])
@login_required
async def delete_habit(habit_id):
    try:
        await _make_api_request("DELETE", f"/habits/{habit_id}")
        flash('Habit deleted successfully!')
        return jsonify({'success': True})
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/habits/log', methods=['POST'])
@login_required
async def log_habit():
    try:
        log_data = {
            "habit_id": int(request.form['habit_id']),
            "date": request.form['date'],
            "is_done": request.form.get('is_done') == 'true',
            "index": int(request.form.get('index', 0))
        }
        await _make_api_request("POST", "/habits/log", json_data=log_data)
        return jsonify({'success': True})
    except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
        return jsonify({'error': str(e)}), 500