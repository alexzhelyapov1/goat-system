from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.models import User
from app.schemas import UserCreate
from pydantic import ValidationError

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
