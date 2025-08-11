# app/cart/__init__.py
from flask import Blueprint

bp = Blueprint('cart', __name__, template_folder='templates', url_prefix='/cart')

from app.cart import routes