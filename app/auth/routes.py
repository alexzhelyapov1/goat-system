from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, make_response, g
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import bp
from app.models import User
from app.schemas import UserCreate
from pydantic import ValidationError
import uuid
from app.queue import redis_conn
import httpx
from app.api_client import make_api_request
from app.auth.jwt import decode_access_token

@bp.route('/telegram/connect', methods=['POST'])
@login_required
def telegram_connect():
    """Generate a token for telegram linking and store it in Redis."""
    token = str(uuid.uuid4())
    redis_conn.set(f"telegram_token:{token}", current_user.id, ex=600)
    flash(f'Your Telegram connection token is: {token}. Use it in your Telegram bot.')
    return jsonify({
        'token': token,
        'bot_username': current_app.config['TELEGRAM_BOT_USERNAME']
    })

@bp.route('/telegram/disconnect', methods=['POST'])
@login_required
def telegram_disconnect():
    """Unlink a telegram account from the user profile."""
    try:
        make_api_request("POST", "/telegram/disconnect")
        flash('Your Telegram account has been unlinked.')
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        flash(f"Could not disconnect Telegram: {e}", "danger")
    return redirect(url_for('auth.profile'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            user_data = UserCreate(username=request.form['username'], password=request.form['password'])
            make_api_request("POST", "/auth/register", json_data=user_data.model_dump())
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('auth.login'))
        except ValidationError as e:
            flash(f"Validation Error: {e.errors()}", 'danger')
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get('detail', 'Registration failed.')
            flash(error_detail, 'danger')
        except httpx.RequestError as e:
            flash(f"Could not connect to the registration service: {e}", "danger")
        return redirect(url_for('auth.register'))
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            # First, get the JWT token from the API
            token_response = make_api_request(
                "POST",
                "/auth/token",
                form_data={"username": request.form['username'], "password": request.form['password']},
            )
            token_data = token_response.json()
            access_token = token_data['access_token']

            # Get user data from the API
            user_response = make_api_request("GET", "/auth/me", token=access_token)
            user_json = user_response.json()

            # Create an in-memory User object for Flask-Login
            user = User(
                id=user_json['id'],
                username=user_json['username'],
                role=user_json['role']
            )

            login_user(user, remember=True)
            
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('access_token', access_token, httponly=True, samesite='Lax')
            return resp

        except httpx.HTTPStatusError as e:
            flash("Invalid username or password.", "danger")
            return redirect(url_for('auth.login'))
        except httpx.RequestError as e:
            flash(f"Could not connect to the login service: {e}", "danger")
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    resp = make_response(redirect(url_for('index')))
    resp.delete_cookie('access_token')
    return resp

@bp.route('/profile')
@login_required
def profile():
    g.db.refresh(current_user)
    return render_template('auth/profile.html', user=current_user)

@bp.route('/trigger-error')
@login_required
def trigger_error():
    raise RuntimeError("This is a test error from the web app.")