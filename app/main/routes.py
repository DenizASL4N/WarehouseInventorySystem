# app/main/routes.py
from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_required
from sqlalchemy import func, desc, asc, case, cast, Numeric, Date
from datetime import datetime, timedelta
from app import db
from app.main import bp
from app.models import User, Product, Order, OrderItem, WarehouseLocation, Supplier
from app.decorators import role_required


@bp.route('/')
@bp.route('/index')
def index():
    return render_template('main/index.html', title='Home Page')


@bp.route('/dashboard')
@login_required
def dashboard():
    user_role = current_user.role
    dashboard_data = {}

    dashboard_data['recent_user_orders'] = Order.query.filter_by(user_id=current_user.id) \
        .order_by(Order.order_date.desc()) \
        .limit(3).all()
    dashboard_data['total_products_in_system'] = Product.query.count()

    if user_role == 'Admin':
        dashboard_data['total_users'] = User.query.count()
        dashboard_data['pending_orders_count'] = Order.query.filter_by(status='Pending').count()
        dashboard_data['total_suppliers'] = Supplier.query.count()
        dashboard_data['total_warehouses'] = WarehouseLocation.query.count()
        dashboard_data['latest_products'] = Product.query.order_by(Product.created_at.desc()).limit(5).all()
        dashboard_data['all_system_orders_count'] = Order.query.count()
    elif user_role == 'WarehouseManager':
        dashboard_data['low_stock_products_count'] = Product.query.filter(
            Product.quantity_in_stock <= Product.low_stock_threshold).count()
        dashboard_data['pending_orders_count'] = Order.query.filter_by(status='Pending').count()
        dashboard_data['total_warehouses'] = WarehouseLocation.query.count()
        dashboard_data['total_suppliers'] = Supplier.query.count()
        today_date = datetime.utcnow().date()
        upcoming_expiry_limit = today_date + timedelta(days=30)
        dashboard_data['expiring_soon_products'] = Product.query.filter(
            Product.expiry_date != None,
            Product.expiry_date >= today_date,
            Product.expiry_date <= upcoming_expiry_limit
        ).order_by(Product.expiry_date.asc()).limit(5).all()
    elif user_role == 'InventoryStaff':
        dashboard_data['low_stock_products_count'] = Product.query.filter(
            Product.quantity_in_stock <= Product.low_stock_threshold).count()
        today_date = datetime.utcnow().date()
        upcoming_expiry_limit_staff = today_date + timedelta(days=15)
        dashboard_data['expiring_soon_count_staff'] = Product.query.filter(
            Product.expiry_date != None,
            Product.expiry_date >= today_date,
            Product.expiry_date <= upcoming_expiry_limit_staff
        ).count()
        dashboard_data['total_products_in_stock_units'] = db.session.query(
            func.sum(Product.quantity_in_stock)).scalar() or 0
    elif user_role == 'SalesTeam':
        today_date = datetime.utcnow().date()
        dashboard_data['orders_today_count'] = Order.query.filter(
            cast(Order.order_date, Date) == today_date
        ).count()
        dashboard_data['sales_today_amount'] = db.session.query(func.sum(Order.total_amount)).filter(
            cast(Order.order_date, Date) == today_date
        ).scalar() or 0.0

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        dashboard_data['top_selling_products_30d'] = db.session.query(
            Product.name,
            Product.id.label('product_id'),
            func.sum(OrderItem.quantity).label('total_sold')
        ).join(OrderItem, Product.id == OrderItem.product_id) \
            .join(Order, OrderItem.order_id == Order.id) \
            .filter(Order.order_date >= thirty_days_ago) \
            .group_by(Product.id, Product.name) \
            .order_by(desc('total_sold')) \
            .limit(5).all()

    return render_template('main/dashboard.html',
                           title='Dashboard',
                           dashboard_data=dashboard_data,
                           user_role=user_role)


# --- Reports Section ---
@bp.route('/reports')
@login_required
@role_required(['Admin', 'WarehouseManager', 'SalesTeam', 'InventoryStaff'])
def reports_index():
    return render_template('main/reports_index.html', title='Reports Dashboard')


@bp.route('/reports/low_stock')
@login_required
@role_required(['Admin', 'WarehouseManager', 'InventoryStaff', 'SalesTeam'])
def low_stock_report():
    low_stock_products = Product.query.filter(
        Product.quantity_in_stock <= Product.low_stock_threshold
    ).order_by(Product.quantity_in_stock.asc()).all()
    return render_template('main/report_low_stock.html',
                           title='Low Stock Products',
                           products=low_stock_products)


@bp.route('/reports/inventory_aging')
@login_required
@role_required(['Admin', 'WarehouseManager', 'SalesTeam', 'InventoryStaff'])
def inventory_aging_report():
    today = datetime.utcnow().date()
    upcoming_expiry_limit = today + timedelta(days=30)
    expiring_soon_products = Product.query.filter(
        Product.expiry_date != None,
        Product.expiry_date >= today,
        Product.expiry_date <= upcoming_expiry_limit
    ).order_by(Product.expiry_date.asc()).all()
    expired_products = Product.query.filter(
        Product.expiry_date != None,
        Product.expiry_date < today
    ).order_by(Product.expiry_date.desc()).all()
    return render_template('main/report_inventory_aging.html',
                           title='Inventory Aging Analysis',
                           expiring_soon=expiring_soon_products,
                           expired=expired_products,
                           today=today)


@bp.route('/reports/products_by_warehouse')
@login_required
@role_required(['Admin', 'WarehouseManager', 'InventoryStaff', 'SalesTeam'])
def products_by_warehouse_report():
    warehouse_order_criteria = [
        case((WarehouseLocation.name == None, 1), else_=0),
        WarehouseLocation.name.asc(), WarehouseLocation.address.asc()
    ]
    warehouses = WarehouseLocation.query.order_by(*warehouse_order_criteria).all()
    warehouses_with_products = []
    for wh in warehouses:
        sorted_products = sorted(wh.products_stored, key=lambda p: p.name)
        warehouses_with_products.append({'warehouse': wh, 'products': sorted_products})
    return render_template('main/report_products_by_warehouse.html',
                           title='Products by Warehouse',
                           warehouses_with_products=warehouses_with_products)


@bp.route('/reports/recent_orders')
@login_required
@role_required(['Admin', 'WarehouseManager', 'SalesTeam', 'InventoryStaff'])
def recent_orders_report():
    days_to_look_back = request.args.get('days', 30, type=int)
    if days_to_look_back <= 0 or days_to_look_back > 365: days_to_look_back = 30
    start_date = datetime.utcnow() - timedelta(days=days_to_look_back)
    query = Order.query.filter(Order.order_date >= start_date)
    recent_orders = query.order_by(Order.order_date.desc()).all()
    return render_template('main/report_recent_orders.html',
                           title=f'Recent Orders (Last {days_to_look_back} Days)',
                           orders=recent_orders,
                           days_filter=days_to_look_back)


@bp.route('/reports/most_profitable_products')
@login_required
@role_required(['Admin', 'WarehouseManager', 'SalesTeam', 'InventoryStaff'])
def most_profitable_products_report():
    profitable_products_query = db.session.query(
        Product.name, Product.id.label('product_id'),
        func.sum(OrderItem.quantity).label('total_quantity_sold'),
        func.sum(OrderItem.quantity * (cast(Product.price, Numeric) - cast(Product.purchase_price, Numeric))).label(
            'total_profit')
    ).join(OrderItem, Product.id == OrderItem.product_id) \
        .filter(Product.purchase_price != None) \
        .group_by(Product.id, Product.name) \
        .order_by(desc('total_profit')) \
        .limit(10).all()
    most_sold_products_query = db.session.query(
        Product.name, Product.id.label('product_id'),
        func.sum(OrderItem.quantity).label('total_quantity_sold')
    ).join(OrderItem, Product.id == OrderItem.product_id) \
        .group_by(Product.id, Product.name) \
        .order_by(desc('total_quantity_sold')) \
        .limit(10).all()
    return render_template('main/report_most_profitable_products.html',
                           title='Most Profitable Products (Top 10)',
                           profitable_products=profitable_products_query,
                           most_sold_products=most_sold_products_query)


@bp.route('/reports/warehouse_capacity')
@login_required
@role_required(['Admin', 'WarehouseManager', 'InventoryStaff'])
def warehouse_capacity_report():
    warehouse_order_criteria = [
        case((WarehouseLocation.name == None, 1), else_=0),
        WarehouseLocation.name.asc(), WarehouseLocation.address.asc()
    ]
    warehouses = WarehouseLocation.query.order_by(*warehouse_order_criteria).all()
    warehouse_data = []
    for wh in warehouses:
        if wh.capacity is not None and wh.capacity > 0:
            current_occupancy_query = db.session.query(func.sum(Product.quantity_in_stock)) \
                .filter(Product.warehouse_id == wh.id) \
                .scalar()
            current_occupancy = current_occupancy_query if current_occupancy_query is not None else 0
            occupancy_percentage = (current_occupancy / wh.capacity) * 100 if wh.capacity > 0 else 0
            warehouse_data.append({
                'id': wh.id, 'name': wh.name if wh.name else wh.address,
                'capacity': wh.capacity, 'current_occupancy': current_occupancy,
                'occupancy_percentage': round(occupancy_percentage, 2)
            })
        else:
            warehouse_data.append({
                'id': wh.id, 'name': wh.name if wh.name else wh.address,
                'capacity': wh.capacity if wh.capacity is not None else 'N/A',
                'current_occupancy': 'N/A', 'occupancy_percentage': 'N/A'
            })
    return render_template('main/report_warehouse_capacity.html',
                           title='Warehouse Capacity Analysis',
                           warehouses_data=warehouse_data)