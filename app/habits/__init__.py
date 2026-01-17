from flask import Blueprint

bp = Blueprint('habits', __name__)

from app.habits import routes
