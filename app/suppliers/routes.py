# app/suppliers/routes.py
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from app import db
from app.suppliers import bp
from app.models import Supplier, Product
from app.forms import SupplierForm, EmptyForm
from app.decorators import can_view_general_data, can_manage_core_data, admin_required


@bp.route('/')
@login_required
@can_view_general_data  # View for Admin, WM, Sales, Staff
def list_suppliers():
    page = request.args.get('page', 1, type=int)
    suppliers_pagination = Supplier.query.order_by(Supplier.name.asc()).paginate(
        page=page, per_page=10, error_out=False
    )
    suppliers_items = suppliers_pagination.items
    delete_forms = {supplier.id: EmptyForm() for supplier in suppliers_items}
    return render_template('suppliers/list_suppliers.html',
                           title='Suppliers',
                           suppliers=suppliers_items,
                           pagination=suppliers_pagination,
                           delete_forms=delete_forms)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
@can_manage_core_data  # Manage for Admin, WM
def add_supplier():
    form = SupplierForm()
    if form.validate_on_submit():
        existing_supplier = Supplier.query.filter_by(name=form.name.data).first()
        if existing_supplier:
            flash('A supplier with this name already exists.', 'warning')
        else:
            new_supplier = Supplier(
                name=form.name.data,
                contact=form.contact_name.data if form.contact_name.data else None,  # Modelde 'contact'
                # contact_email=form.contact_email.data if hasattr(form, 'contact_email') and form.contact_email.data else None, # Eğer modelde varsa
                # contact_phone=form.contact_phone.data if hasattr(form, 'contact_phone') and form.contact_phone.data else None, # Eğer modelde varsa
                address=form.address.data if form.address.data else None
            )
            db.session.add(new_supplier)
            db.session.commit()
            flash(f'Supplier "{new_supplier.name}" has been added successfully!', 'success')
            return redirect(url_for('suppliers.list_suppliers'))
    return render_template('suppliers/supplier_form.html', title='Add New Supplier', form=form, legend='New Supplier')


@bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@can_manage_core_data  # Manage for Admin, WM
def edit_supplier(supplier_id):
    supplier_to_edit = db.session.get(Supplier, supplier_id) or abort(404)
    form = SupplierForm()
    if form.validate_on_submit():
        if supplier_to_edit.name != form.name.data:
            existing_supplier = Supplier.query.filter(Supplier.id != supplier_id,
                                                      Supplier.name == form.name.data).first()
            if existing_supplier:
                flash('Another supplier with this name already exists.', 'warning')
                return render_template('suppliers/supplier_form.html', title='Edit Supplier', form=form,
                                       legend=f'Edit: {supplier_to_edit.name}')

        supplier_to_edit.name = form.name.data
        supplier_to_edit.contact = form.contact_name.data if form.contact_name.data else None  # Modelde 'contact'
        # if hasattr(form, 'contact_email'): supplier_to_edit.contact_email = form.contact_email.data if form.contact_email.data else None
        # if hasattr(form, 'contact_phone'): supplier_to_edit.contact_phone = form.contact_phone.data if form.contact_phone.data else None
        supplier_to_edit.address = form.address.data if form.address.data else None
        db.session.commit()
        flash(f'Supplier "{supplier_to_edit.name}" has been updated successfully!', 'info')
        return redirect(url_for('suppliers.list_suppliers'))
    elif request.method == 'GET':
        form.process(obj=supplier_to_edit)
        form.contact_name.data = supplier_to_edit.contact  # Modelde 'contact'
        # if hasattr(form, 'contact_email'): form.contact_email.data = supplier_to_edit.contact_email
        # if hasattr(form, 'contact_phone'): form.contact_phone.data = supplier_to_edit.contact_phone
    return render_template('suppliers/supplier_form.html', title='Edit Supplier', form=form,
                           legend=f'Edit: {supplier_to_edit.name}')


@bp.route('/<int:supplier_id>/delete', methods=['POST'])
@login_required
@admin_required  # Only Admin (veya @can_manage_core_data)
def delete_supplier(supplier_id):
    supplier_to_delete = db.session.get(Supplier, supplier_id) or abort(404)
    if supplier_to_delete.products_supplied.first():
        flash(
            f'Supplier "{supplier_to_delete.name}" cannot be deleted because it is associated with existing products.',
            'danger')
        return redirect(url_for('suppliers.list_suppliers'))
    supplier_name = supplier_to_delete.name
    db.session.delete(supplier_to_delete)
    db.session.commit()
    flash(f'Supplier "{supplier_name}" has been deleted.', 'success')
    return redirect(url_for('suppliers.list_suppliers'))