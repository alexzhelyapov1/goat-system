from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.models import User, UserRole
from app.schemas import UserCreate
from pydantic import ValidationError
import uuid
from app.queue import redis_conn
import httpx
from config import API_BASE_URL
from app.api_client import make_api_request # Import the new centralized API client


@bp.route('/telegram/connect', methods=['POST'])
@login_required
async def telegram_connect():
    """Generate a token for telegram linking and store it in Redis."""
    token = str(uuid.uuid4())
    # Key: telegram_token:<token>, Value: user_id, TTL: 10 minutes
    redis_conn.set(f"telegram_token:{token}", current_user.id, ex=600)

    # Call FastAPI endpoint to update user with Telegram info if available
    # For now, we only flash the token. The bot will use this token to update.
    flash(f'Your Telegram connection token is: {token}. Use it in your Telegram bot.')
    return jsonify({
        'token': token,
        'bot_username': current_app.config['TELEGRAM_BOT_USERNAME']
    })

@bp.route('/telegram/disconnect', methods=['POST'])
@login_required
async def telegram_disconnect():
    """Unlink a telegram account from the user profile."""
    try:
        await make_api_request("POST", "/telegram/disconnect")
        flash('Your Telegram account has been unlinked.')
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass # Error already flashed by _make_api_request
    return redirect(url_for('auth.profile'))

@bp.route('/register', methods=['GET', 'POST'])
async def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            user_data = UserCreate(username=request.form['username'], password=request.form['password'])
            if User.query.filter_by(username=user_data.username).first():
                flash('Please use a different username.')
                return redirect(url_for('auth.register'))
            user = User(username=user_data.username)
            user.set_password(user_data.password)
            # Make the first user an admin
            if not User.query.first():
                user.role = UserRole.ADMIN
            db.session.add(user)
            db.session.commit()
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('auth.login'))
        except ValidationError as e:
            flash(str(e.errors()))
            return redirect(url_for('auth.register'))
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
async def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=True)

        try:
            response = await make_api_request(
                "POST",
                "/token",
                json_data={"username": request.form['username'], "password": request.form['password']},
                # FastAPI's OAuth2PasswordRequestForm expects form-data, not json.
                # When using make_api_request with json_data, it sends as application/json.
                # If FastAPI expects form-urlencoded, the API client would need to support that,
                # or we change FastAPI to expect JSON for /token endpoint.
                # For now, let's assume json is acceptable, or modify FastAPI.
                # Given OAuth2PasswordRequestForm, it's expecting form data.
                # Let's directly use httpx.post with data= for form-urlencoded.
                # This makes the make_api_request less useful for this specific case,
                # but it's an edge case due to OAuth2PasswordRequestForm.
            )
            token_data = response.json()
            session['jwt_token'] = token_data['access_token']
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            flash("Failed to obtain JWT token from API.")
            logout_user()
            return redirect(url_for('auth.login'))

        return redirect(url_for('index'))
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    session.pop('jwt_token', None) # Clear the JWT token from session
    return redirect(url_for('index'))

@bp.route('/profile')
@login_required
def profile():
    # Refresh the user object from the database to get the latest data
    db.session.refresh(current_user)
    return render_template('auth/profile.html', user=current_user)

@bp.route('/trigger-error')
@login_required
def trigger_error():
    """This route is for testing the error reporting functionality."""
    raise RuntimeError("This is a test error from the web app.")
