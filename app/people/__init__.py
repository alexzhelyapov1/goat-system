from flask import Blueprint

bp = Blueprint('people', __name__)

from app.people import routes
