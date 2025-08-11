# app/warehouses/routes.py
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from sqlalchemy import case
from app import db
from app.warehouses import bp
from app.models import WarehouseLocation, Product
from app.forms import WarehouseLocationForm, EmptyForm
from app.decorators import can_view_general_data, can_manage_core_data, admin_required

@bp.route('/')
@login_required
@can_view_general_data # View for Admin, WM, Sales, Staff
def list_warehouses():
    page = request.args.get('page', 1, type=int)
    warehouse_order_criteria = [
        case((WarehouseLocation.name == None, 1), else_=0),
        WarehouseLocation.name.asc(), WarehouseLocation.address.asc()
    ]
    warehouses_pagination = WarehouseLocation.query.order_by(*warehouse_order_criteria).paginate(
        page=page, per_page=10, error_out=False
    )
    warehouses_items = warehouses_pagination.items
    delete_forms = {wh.id: EmptyForm() for wh in warehouses_items}
    return render_template('warehouses/list_warehouses.html',
                           title='Warehouse Locations',
                           warehouses=warehouses_items,
                           pagination=warehouses_pagination,
                           delete_forms=delete_forms)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@can_manage_core_data # Manage for Admin, WM
def add_warehouse():
    form = WarehouseLocationForm()
    if form.validate_on_submit():
        existing_by_address = WarehouseLocation.query.filter_by(address=form.address.data).first()
        if existing_by_address:
            flash('A warehouse with this address already exists.', 'warning')
        elif form.name.data and WarehouseLocation.query.filter_by(name=form.name.data).first():
            flash('A warehouse with this name already exists.', 'warning')
        else:
            new_warehouse = WarehouseLocation(
                name=form.name.data if form.name.data else None,
                address=form.address.data,
                capacity=form.capacity.data if form.capacity.data is not None else None
            )
            db.session.add(new_warehouse)
            db.session.commit()
            flash(f'Warehouse location "{new_warehouse.name or new_warehouse.address}" has been added successfully!', 'success')
            return redirect(url_for('warehouses.list_warehouses'))
    return render_template('warehouses/warehouse_form.html', title='Add New Warehouse Location', form=form, legend='New Warehouse Location')

@bp.route('/<int:warehouse_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_core_data # Manage for Admin, WM
def edit_warehouse(warehouse_id):
    warehouse_to_edit = db.session.get(WarehouseLocation, warehouse_id) or abort(404)
    form = WarehouseLocationForm()
    if form.validate_on_submit():
        if warehouse_to_edit.address != form.address.data:
            existing_by_address = WarehouseLocation.query.filter(WarehouseLocation.id != warehouse_id, WarehouseLocation.address == form.address.data).first()
            if existing_by_address:
                flash('Another warehouse with this address already exists.', 'warning')
                return render_template('warehouses/warehouse_form.html', title='Edit Warehouse Location', form=form, legend=f'Edit: {warehouse_to_edit.name or warehouse_to_edit.address}')
        if form.name.data and warehouse_to_edit.name != form.name.data:
            existing_by_name = WarehouseLocation.query.filter(WarehouseLocation.id != warehouse_id, WarehouseLocation.name == form.name.data).first()
            if existing_by_name:
                flash('Another warehouse with this name already exists.', 'warning')
                return render_template('warehouses/warehouse_form.html', title='Edit Warehouse Location', form=form, legend=f'Edit: {warehouse_to_edit.name or warehouse_to_edit.address}')
        warehouse_to_edit.name = form.name.data if form.name.data else None
        warehouse_to_edit.address = form.address.data
        warehouse_to_edit.capacity = form.capacity.data if form.capacity.data is not None else None
        db.session.commit()
        flash(f'Warehouse location "{warehouse_to_edit.name or warehouse_to_edit.address}" has been updated successfully!', 'info')
        return redirect(url_for('warehouses.list_warehouses'))
    elif request.method == 'GET':
        form.process(obj=warehouse_to_edit)
    return render_template('warehouses/warehouse_form.html', title='Edit Warehouse Location', form=form, legend=f'Edit: {warehouse_to_edit.name or warehouse_to_edit.address}')

@bp.route('/<int:warehouse_id>/delete', methods=['POST'])
@login_required
@admin_required # Only Admin (veya @can_manage_core_data)
def delete_warehouse(warehouse_id):
    warehouse_to_delete = db.session.get(WarehouseLocation, warehouse_id) or abort(404)
    if warehouse_to_delete.products_stored.first():
        flash(f'Warehouse "{warehouse_to_delete.name or warehouse_to_delete.address}" cannot be deleted because it has products stored in it.', 'danger')
        return redirect(url_for('warehouses.list_warehouses'))
    warehouse_identifier = warehouse_to_delete.name or warehouse_to_delete.address
    db.session.delete(warehouse_to_delete)
    db.session.commit()
    flash(f'Warehouse location "{warehouse_identifier}" has been deleted.', 'success')
    return redirect(url_for('warehouses.list_warehouses'))