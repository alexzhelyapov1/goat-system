from flask import Flask, redirect, url_for, session, render_template
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from app.extensions import db, login_manager, migrate
import config
from sqlalchemy import event
from sqlalchemy.engine import Engine


def create_app(config_class=config.Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['SESSION_PERMANENT'] = True

    db.init_app(app)

    # Enable WAL mode for SQLite to prevent "database is locked" errors
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.before_request
    def before_request():
        session.permanent = True

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp)

    from app.habits import bp as habits_bp
    app.register_blueprint(habits_bp)

    from app.movies import bp as movies_bp
    app.register_blueprint(movies_bp)


    from app.calendar import bp as calendar_bp
    app.register_blueprint(calendar_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Register CLI commands
    from app import cli
    cli.register_commands(app)

    @app.route('/health')
    def health_check():
        return 'OK'

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('tasks.tasks'))
        return redirect(url_for('auth.login'))

    from app.telegram_utils import send_telegram_message, run_async_in_new_loop
    from app.models import User
    import traceback
    import asyncio

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log the error
        app.logger.error(f"Unhandled Exception: {e}", exc_info=True)

        # Build error message for Telegram
        error_message = f"🚨 *Application Error (Web Service)* 🚨\n\n" \
                        f"**Error Type:** `{type(e).__name__}`\n" \
                        f"**Message:** `{str(e)}`\n" \
                        f"**Traceback:**\n```\n{traceback.format_exc()}\n```"

        # Try to send message to 'alex'
        with app.app_context():
            alex_user = User.query.filter_by(username='alex').first()
            if alex_user and alex_user.telegram_chat_id:
                try:
                    # Run the async function in a new event loop
                    run_async_in_new_loop(send_telegram_message(
                        chat_id=alex_user.telegram_chat_id,
                        message=error_message,
                        app_instance=app
                    ))
                except Exception as tg_e:
                    app.logger.error(f"Failed to send Telegram error report: {tg_e}", exc_info=True)
            else:
                app.logger.warning("Could not find user 'alex' or their Telegram chat ID for error reporting.")

        # For the user, return a generic error page or message
        return "An internal server error occurred.", 500

    return app
