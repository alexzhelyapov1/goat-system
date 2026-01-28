from functools import wraps
from flask import redirect, url_for, render_template, flash, request, jsonify, session
from flask_login import login_required, current_user
from app.admin import bp
from app.models import User, UserRole
from app import db
import httpx
from pydantic import TypeAdapter
from typing import List
from app.schemas import UserSchema


API_BASE_URL = "http://api:5001"

async def _make_api_request(method: str, endpoint: str, item_id: int = None, json_data: dict = None, params: dict = None):
    headers = {}
    if 'jwt_token' in session:
        headers["Authorization"] = f"Bearer {session['jwt_token']}"

    url = f"{API_BASE_URL}{endpoint}"
    if item_id:
        url = f"{url}{item_id}"

    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await client.post(url, json=json_data, headers=headers, params=params)
            elif method == "PUT":
                response = await client.put(url, json=json_data, headers=headers, params=params)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
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
async def users():
    try:
        response = await _make_api_request("GET", "/admin/users")
        users_data = response.json()
        all_users = TypeAdapter(List[UserSchema]).validate_python(users_data)
    except httpx.RequestError:
        all_users = []
    all_roles = [role.name for role in UserRole]
    return render_template('admin/users.html', users=all_users, roles=all_roles)

@bp.route('/users/<int:user_id>/set_role', methods=['POST'])
@admin_required
async def set_role(user_id):
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
        response = await _make_api_request("POST", f"/admin/users/{user_id}/set_role", json_data={"new_role": new_role.name})
        user_to_update = TypeAdapter(UserSchema).validate_python(response.json())
        flash(f"Successfully updated {user_to_update.username}'s role to {user_to_update.role.name}.", "success")
    except httpx.RequestError:
        pass # Error message is flashed by _make_api_request

    return redirect(url_for('admin.users'))
