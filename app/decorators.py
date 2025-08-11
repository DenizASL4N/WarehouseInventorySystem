# app/decorators.py
from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from urllib.parse import urlparse

def role_required(allowed_roles):
    if not isinstance(allowed_roles, list):
        allowed_roles = [allowed_roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))

            if not hasattr(current_user, 'role') or current_user.role not in allowed_roles:
                flash(f"Access Denied: You do not have the required permissions ({', '.join(allowed_roles)}) to view this page.", "danger")
                safe_redirect = url_for('main.dashboard' if current_user.is_authenticated else 'main.index')
                if request.referrer and urlparse(request.referrer).netloc == urlparse(request.url_root).netloc and request.referrer != request.url:
                    return redirect(safe_redirect)
                return redirect(safe_redirect)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required(['Admin'])(f)

def manager_or_admin_required(f):
    return role_required(['Admin', 'WarehouseManager'])(f)

def can_view_general_data(f):
    return role_required(['Admin', 'WarehouseManager', 'SalesTeam', 'InventoryStaff'])(f)

def can_manage_core_data(f):
    return role_required(['Admin', 'WarehouseManager'])(f)

# ESKİ RAPOR DECORATOR'LARI YERİNE YENİSİ (veya direkt role_required kullanımı)
# def can_view_operational_reports(f):
#     return role_required(['Admin', 'WarehouseManager', 'InventoryStaff', 'SalesTeam'])(f)

# def can_view_sales_reports(f):
#     return role_required(['Admin', 'WarehouseManager', 'SalesTeam'])(f)

# YENİ DECORATOR: Tüm raporları görebilecek roller için
def can_view_all_reports(f):
    return role_required(['Admin', 'WarehouseManager', 'SalesTeam', 'InventoryStaff'])(f)