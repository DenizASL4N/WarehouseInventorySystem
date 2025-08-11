# app/products/routes.py
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from sqlalchemy import case
from app import db
from app.products import bp
from app.models import Product, Supplier, WarehouseLocation
from app.forms import ProductForm, EmptyForm
from app.decorators import admin_required, can_manage_core_data, can_view_general_data


@bp.route('/')
@login_required
@can_view_general_data  # All defined roles can view the list
def list_products():
    page = request.args.get('page', 1, type=int)
    products_pagination = Product.query.order_by(Product.name.asc()).paginate(
        page=page, per_page=10, error_out=False
    )
    products_items = products_pagination.items
    delete_forms = {product.id: EmptyForm() for product in products_items}

    return render_template('products/list_products.html',
                           title='Products',
                           products=products_items,
                           pagination=products_pagination,
                           delete_forms=delete_forms)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
@can_manage_core_data  # Only Admin or WarehouseManager can add
def add_product():
    form = ProductForm()
    form.supplier_id.choices = [(0, '--- Select Supplier (Optional) ---')] + \
                               [(s.id, s.name) for s in Supplier.query.order_by(Supplier.name.asc()).all()]
    warehouse_order_criteria = [
        case((WarehouseLocation.name == None, 1), else_=0),
        WarehouseLocation.name.asc(), WarehouseLocation.address.asc()
    ]
    form.warehouse_id.choices = [(0, '--- Select Warehouse (Optional) ---')] + \
                                [(w.id, w.name if w.name else w.address) for w in
                                 WarehouseLocation.query.order_by(*warehouse_order_criteria).all()]
    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data, category=form.category.data if form.category.data else None,
            quantity_in_stock=form.quantity_in_stock.data, price=form.price.data,
            expiry_date=form.expiry_date.data, description=form.description.data if form.description.data else None,
            supplier_id=form.supplier_id.data if form.supplier_id.data != 0 else None,
            warehouse_id=form.warehouse_id.data if form.warehouse_id.data != 0 else None,
            purchase_price=form.purchase_price.data if hasattr(form,
                                                               'purchase_price') and form.purchase_price.data is not None else None,
            low_stock_threshold=form.low_stock_threshold.data if hasattr(form,
                                                                         'low_stock_threshold') and form.low_stock_threshold.data is not None else 10
        )
        db.session.add(new_product)
        db.session.commit()
        flash(f'Product "{new_product.name}" has been added successfully!', 'success')
        return redirect(url_for('products.list_products'))
    return render_template('products/product_form.html', title='Add New Product', form=form, legend='New Product')


@bp.route('/<int:product_id>')
@login_required
@can_view_general_data  # All defined roles can view details
def product_detail(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    return render_template('products/product_detail.html', title=product.name, product=product)


@bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_core_data  # Only Admin or WarehouseManager can edit
def edit_product(product_id):
    product_to_edit = db.session.get(Product, product_id) or abort(404)
    form = ProductForm()
    form.supplier_id.choices = [(0, '--- Select Supplier (Optional) ---')] + \
                               [(s.id, s.name) for s in Supplier.query.order_by(Supplier.name.asc()).all()]
    warehouse_order_criteria = [
        case((WarehouseLocation.name == None, 1), else_=0),
        WarehouseLocation.name.asc(), WarehouseLocation.address.asc()
    ]
    form.warehouse_id.choices = [(0, '--- Select Warehouse (Optional) ---')] + \
                                [(w.id, w.name if w.name else w.address) for w in
                                 WarehouseLocation.query.order_by(*warehouse_order_criteria).all()]
    if form.validate_on_submit():
        product_to_edit.name = form.name.data
        product_to_edit.category = form.category.data if form.category.data else None
        product_to_edit.quantity_in_stock = form.quantity_in_stock.data
        product_to_edit.price = form.price.data
        product_to_edit.expiry_date = form.expiry_date.data
        product_to_edit.description = form.description.data if form.description.data else None
        product_to_edit.supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        product_to_edit.warehouse_id = form.warehouse_id.data if form.warehouse_id.data != 0 else None
        if hasattr(form,
                   'purchase_price'): product_to_edit.purchase_price = form.purchase_price.data if form.purchase_price.data is not None else product_to_edit.purchase_price
        if hasattr(form,
                   'low_stock_threshold'): product_to_edit.low_stock_threshold = form.low_stock_threshold.data if form.low_stock_threshold.data is not None else product_to_edit.low_stock_threshold
        db.session.commit()
        flash(f'Product "{product_to_edit.name}" has been updated successfully!', 'info')
        return redirect(url_for('products.list_products'))
    elif request.method == 'GET':
        form.process(obj=product_to_edit)
        if product_to_edit.supplier_id:
            form.supplier_id.data = product_to_edit.supplier_id
        else:
            form.supplier_id.data = 0
        if product_to_edit.warehouse_id:
            form.warehouse_id.data = product_to_edit.warehouse_id
        else:
            form.warehouse_id.data = 0
    return render_template('products/product_form.html', title='Edit Product', form=form,
                           legend=f'Edit: {product_to_edit.name}')


@bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required  # Only Admin can delete
def delete_product(product_id):
    product_to_delete = db.session.get(Product, product_id) or abort(404)
    product_name = product_to_delete.name
    if product_to_delete.order_items.first():
        flash(f'Product "{product_name}" cannot be deleted because it is part of existing orders.', 'danger')
        return redirect(url_for('products.list_products'))
    db.session.delete(product_to_delete)
    db.session.commit()
    flash(f'Product "{product_name}" has been deleted.', 'success')
    return redirect(url_for('products.list_products'))