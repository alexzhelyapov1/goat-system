from functools import wraps
from flask import redirect, url_for, render_template, flash, request
from flask_login import login_required, current_user
from app.admin import bp
from app.models import User, UserRole
from app import db

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.ADMIN:
            flash("You do not have permission to access this page.")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/users')
@admin_required
def users():
    all_users = User.query.all()
    all_roles = [role.name for role in UserRole]
    return render_template('admin/users.html', users=all_users, roles=all_roles)

@bp.route('/users/<int:user_id>/set_role', methods=['POST'])
@admin_required
def set_role(user_id):
    user_to_update = User.query.get_or_404(user_id)
    new_role_name = request.form.get('role')

    if user_to_update.id == current_user.id:
        flash("For security reasons, you cannot change your own role.", "danger")
        return redirect(url_for('admin.users'))

    try:
        new_role = UserRole[new_role_name]
    except KeyError:
        flash(f"Invalid role '{new_role_name}'.", "danger")
        return redirect(url_for('admin.users'))

    user_to_update.role = new_role
    db.session.commit()

    flash(f"Successfully updated {user_to_update.username}'s role to {new_role.name}.", "success")
    return redirect(url_for('admin.users'))
