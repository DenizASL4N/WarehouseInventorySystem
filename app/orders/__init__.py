# app/orders/__init__.py
from flask import Blueprint

bp = Blueprint('orders', __name__, template_folder='templates', url_prefix='/orders')

from app.orders import routes