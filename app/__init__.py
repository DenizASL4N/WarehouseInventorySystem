# app/__init__.py
from flask import Flask, session
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = "Please log in to access this page."
login.login_message_category = "info"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.products import bp as products_bp
    app.register_blueprint(products_bp)

    from app.suppliers import bp as suppliers_bp
    app.register_blueprint(suppliers_bp)

    from app.warehouses import bp as warehouses_bp
    app.register_blueprint(warehouses_bp)

    from app.cart import bp as cart_bp
    app.register_blueprint(cart_bp)

    from app.orders import bp as orders_bp
    app.register_blueprint(orders_bp)

    from app.admin import bp as admin_bp  # Admin Blueprint'ini import et
    app.register_blueprint(admin_bp)  # Admin Blueprint'ini kaydet (url_prefix='/admin' __init__.py'sinde)

    with app.app_context():
        from . import models

    @app.context_processor
    def utility_processor():
        def get_cart_item_count():
            cart = session.get('cart', {})
            return len(cart) if cart is not None else 0

        return {
            'current_year': datetime.utcnow().year,
            'cart_item_count': get_cart_item_count()
        }

    return app