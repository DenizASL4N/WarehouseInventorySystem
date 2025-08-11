# app/admin/routes.py
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.models import User
from app.forms import AdminUserForm, EmptyForm, USER_ROLE_CHOICES  # USER_ROLE_CHOICES'ı da import edebiliriz
from app.decorators import admin_required
from wtforms.validators import DataRequired  # add_user'da şifre için dinamik olarak eklenecek


@bp.route('/users')
@login_required
@admin_required
def list_users():
    page = request.args.get('page', 1, type=int)
    users_pagination = User.query.order_by(User.username.asc()).paginate(
        page=page, per_page=10, error_out=False
    )
    users_items = users_pagination.items
    delete_forms = {user.id: EmptyForm() for user in users_items}
    return render_template('admin/list_users.html',
                           title='Manage Users',
                           users=users_items,
                           pagination=users_pagination,
                           delete_forms=delete_forms)


@bp.route('/user/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = AdminUserForm()

    # Dynamically add DataRequired for password fields only for new user creation
    original_password_validators = list(form.password.validators)
    original_password2_validators = list(form.password2.validators)

    if request.method == 'POST':
        # Add validators for new user
        form.password.validators.append(DataRequired(message="Password is required for new user."))
        if form.password.data:  # Only add EqualTo if password has data, to avoid error if password is blank
            form.password2.validators.append(DataRequired(message="Please repeat the password."))
            # EqualTo is already there, should work fine.

    if form.validate_on_submit():
        existing_user_by_username = User.query.filter_by(username=form.username.data).first()
        if existing_user_by_username:
            flash('This username is already taken.', 'danger')
        elif User.query.filter_by(email=form.email.data).first():
            flash('This email address is already registered.', 'danger')
        else:
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data,
                name=form.name.data if form.name.data else None,
                contact_info=form.contact_info.data if form.contact_info.data else None,
                is_active=form.is_active.data
            )
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            flash(f'User "{new_user.username}" has been created successfully!', 'success')
            return redirect(url_for('admin.list_users'))

    # Restore original validators for GET request or if validation failed, to avoid issues on re-render
    form.password.validators = original_password_validators
    form.password2.validators = original_password2_validators

    return render_template('admin/user_form.html', title='Add New User', form=form, legend='Create New User',
                           USER_ROLE_CHOICES=USER_ROLE_CHOICES)


@bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user_to_edit = db.session.get(User, user_id) or abort(404)
    form = AdminUserForm(obj=user_to_edit, original_username=user_to_edit.username, original_email=user_to_edit.email)

    if form.validate_on_submit():
        user_to_edit.username = form.username.data
        user_to_edit.email = form.email.data
        user_to_edit.name = form.name.data if form.name.data else user_to_edit.name
        user_to_edit.contact_info = form.contact_info.data if form.contact_info.data else user_to_edit.contact_info
        user_to_edit.role = form.role.data
        user_to_edit.is_active = form.is_active.data

        if form.password.data:
            if not form.password2.data:
                form.password2.errors.append("Please repeat the new password.")
            elif form.password.data != form.password2.data:
                # EqualTo validator should handle this, but an explicit check can be added
                form.password2.errors.append("Passwords must match.")
            else:
                user_to_edit.set_password(form.password.data)

        if not form.errors:  # If no errors after custom password check
            db.session.commit()
            flash(f'User "{user_to_edit.username}" has been updated successfully!', 'info')
            return redirect(url_for('admin.list_users'))

    elif request.method == 'GET':
        form.password.data = ""
        form.password2.data = ""

    return render_template('admin/user_form.html', title='Edit User', form=form,
                           legend=f'Edit User: {user_to_edit.username}', USER_ROLE_CHOICES=USER_ROLE_CHOICES,
                           user_id=user_id)


@bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = db.session.get(User, user_id) or abort(404)
    if user_to_delete.id == current_user.id:
        flash("You cannot delete your own administrator account.", "danger")
        return redirect(url_for('admin.list_users'))

    if user_to_delete.username == 'admin' and user_to_delete.role == 'Admin':  # Basic protection for a default admin
        flash("The primary admin account cannot be deleted.", "danger")
        return redirect(url_for('admin.list_users'))

    if user_to_delete.orders_placed.first():
        flash(
            f"User '{user_to_delete.username}' has existing orders and cannot be deleted. Consider deactivating the user instead.",
            "warning")
        # Option to deactivate:
        # user_to_delete.is_active = False
        # db.session.commit()
        # flash(f"User '{user_to_delete.username}' has been deactivated due to existing orders.", "info")
    else:
        username_deleted = user_to_delete.username
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'User "{username_deleted}" has been deleted.', 'success')
    return redirect(url_for('admin.list_users'))