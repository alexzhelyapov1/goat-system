from flask import Flask, redirect, url_for, session, render_template, current_app
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from app.extensions import db, login_manager, migrate
import config
from sqlalchemy import event
from sqlalchemy.engine import Engine
import httpx
import traceback
import asyncio


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

    API_BASE_URL = "http://api:5001" # Define API_BASE_URL here or import from config

    async def _make_api_request_for_error_handler(method: str, endpoint: str, json_data: dict = None):
        headers = {}
        # No JWT token for error reporting as it's an unauthenticated endpoint in FastAPI
        # if 'jwt_token' in session:
        #     headers["Authorization"] = f"Bearer {session['jwt_token']}"

        url = f"{API_BASE_URL}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, json=json_data, headers=headers)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                app.logger.error(f"API Error in error handler: {e.response.status_code} - {e.response.text}", exc_info=True)
                raise
            except httpx.RequestError as e:
                app.logger.error(f"Network Error in error handler: Could not connect to API - {e}", exc_info=True)
                raise

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
        
        admin_chat_id = current_app.config.get('TELEGRAM_ADMIN_CHAT_ID')
        if not admin_chat_id:
            app.logger.warning("TELEGRAM_ADMIN_CHAT_ID not configured. Cannot send Telegram error report.")
            
        if admin_chat_id:
            message_data = {
                "chat_id": admin_chat_id,
                "message": error_message
            }
            # Run the async _make_api_request_for_error_handler in a new event loop
            try:
                # Need to use run_async_in_new_loop for calling async from sync context
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                    _make_api_request_for_error_handler("POST", "/telegram/send_error_report", json_data=message_data)
                )
            except Exception as tg_e:
                app.logger.error(f"Failed to send Telegram error report via API: {tg_e}", exc_info=True)

        # For the user, return a generic error page or message
        return "An internal server error occurred.", 500

    return app
