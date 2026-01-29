from functools import wraps
from flask import redirect, url_for, render_template, flash, request, session
from flask_login import login_required, current_user
from app.admin import bp
from app.models import User, UserRole
from app.api_client import make_api_request
from pydantic import TypeAdapter
from typing import List
from app.schemas import UserSchema
from httpx import RequestError


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.ADMIN:
            flash("You do not have permission to access this page.")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/users')
@admin_required
def users():
    try:
        response = make_api_request("GET", "/admin/users")
        users_data = response.json()
        all_users = TypeAdapter(List[UserSchema]).validate_python(users_data)
    except RequestError as e:
        flash(f"Could not load users: {e}", "danger")
        all_users = []
    all_roles = [role.name for role in UserRole]
    return render_template('admin/users.html', users=all_users, roles=all_roles)

@bp.route('/users/<int:user_id>/set_role', methods=['POST'])
@admin_required
def set_role(user_id):
    new_role_name = request.form.get('role')

    if user_id == current_user.id:
        flash("For security reasons, you cannot change your own role.", "danger")
        return redirect(url_for('admin.users'))

    try:
        new_role = UserRole[new_role_name]
    except KeyError:
        flash(f"Invalid role '{new_role_name}'.", "danger")
        return redirect(url_for('admin.users'))

    try:
        response = make_api_request("POST", f"/admin/users/{user_id}/set_role", json_data={"new_role": new_role.name})
        user_to_update = TypeAdapter(UserSchema).validate_python(response.json())
        flash(f"Successfully updated {user_to_update.username}'s role to {user_to_update.role.name}.", "success")
    except RequestError as e:
        flash(f"Could not set role: {e}", "danger")

    return redirect(url_for('admin.users'))
