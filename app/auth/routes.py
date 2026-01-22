from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.models import User, UserRole
from app.schemas import UserCreate
from pydantic import ValidationError
import uuid
from app.queue import redis_conn

@bp.route('/telegram/connect', methods=['POST'])
@login_required
def telegram_connect():
    """Generate a token for telegram linking and store it in Redis."""
    token = str(uuid.uuid4())
    # Key: telegram_token:<token>, Value: user_id, TTL: 10 minutes
    redis_conn.set(f"telegram_token:{token}", current_user.id, ex=600)
    return jsonify({
        'token': token,
        'bot_username': current_app.config['TELEGRAM_BOT_USERNAME']
    })

@bp.route('/telegram/disconnect', methods=['POST'])
@login_required
def telegram_disconnect():
    """Unlink a telegram account from the user profile."""
    current_user.telegram_chat_id = None
    current_user.telegram_username = None
    db.session.commit()
    flash('Your Telegram account has been unlinked.')
    return redirect(url_for('auth.profile'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
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
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=True)
        return redirect(url_for('index'))
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
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

