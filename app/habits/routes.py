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
    return render_template('habits/habits_list.html')
