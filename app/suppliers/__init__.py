# app/suppliers/__init__.py
from flask import Blueprint

bp = Blueprint('suppliers', __name__, template_folder='templates', url_prefix='/suppliers')

from app.suppliers import routes