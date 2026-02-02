import click
from app.database import SessionLocal
from app.models import User, UserRole

def register_commands(app):
    @app.cli.group()
    def role():
        """Manage user roles."""
        pass

    @role.command('set')
    @click.argument('username')
    @click.argument('role_name')
    def set_role(username, role_name):
        """Set the role for a user."""
        db_session = SessionLocal()
        try:
            user = db_session.query(User).filter_by(username=username).first()
            if not user:
                click.echo(f"Error: User '{username}' not found.")
                return

            try:
                new_role = UserRole[role_name.upper()]
            except KeyError:
                click.echo(f"Error: Invalid role name '{role_name}'. Available roles: {[r.name for r in UserRole]}")
                return

            user.role = new_role
            db_session.commit()
            click.echo(f"User '{username}' role set to '{new_role.name}'.")
        finally:
            db_session.close()

    @role.command('unset')
    @click.argument('username')
    def unset_role(username):
        """Unset the role for a user (sets to default USER role)."""
        db_session = SessionLocal()
        try:
            user = db_session.query(User).filter_by(username=username).first()
            if not user:
                click.echo(f"Error: User '{username}' not found.")
                return

            user.role = UserRole.USER
            db_session.commit()
            click.echo(f"User '{username}' role reset to '{UserRole.USER.name}'.")
        finally:
            db_session.close()
