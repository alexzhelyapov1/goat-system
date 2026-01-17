from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from app.extensions import db, login_manager, migrate
import config

def create_app(config_class=config.Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp)

    from app.habits import bp as habits_bp
    app.register_blueprint(habits_bp)

    from app.movies import bp as movies_bp
    app.register_blueprint(movies_bp)

    from app.people import bp as people_bp
    app.register_blueprint(people_bp)

    from app.calendar import bp as calendar_bp
    app.register_blueprint(calendar_bp)

    from app.scheduler import init_scheduler
    init_scheduler(app)

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('tasks.tasks'))
        return redirect(url_for('auth.login'))

    return app
