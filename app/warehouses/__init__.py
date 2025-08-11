# app/warehouses/__init__.py
from flask import Blueprint

bp = Blueprint('warehouses', __name__, template_folder='templates', url_prefix='/warehouses')

from app.warehouses import routes