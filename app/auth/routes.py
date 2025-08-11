# app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse  # For safe redirection

from app import db
from app.auth import bp
from app.forms import LoginForm, RegistrationForm  # Import from app.forms
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))  # Redirect to dashboard if already logged in

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.username}!', 'success')

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':  # Ensure next_page is safe
            next_page = url_for('main.dashboard')  # Default redirect to dashboard
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('main.index'))  # Redirect to home page after logout


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))  # Redirect if already logged in

    form = RegistrationForm()
    if form.validate_on_submit():
        # Ensure the 'role' field in your User model is handled.
        # If 'role' is nullable=False, you must provide a value.
        # Example: role=form.role.data if you added a role field to RegistrationForm
        # or a default role:
        user = User(username=form.username.data,
                    email=form.email.data,
                    role='InventoryStaff'  # Default role, or from form if you added it
                    # If you added name, contact_info to RegistrationForm in forms.py:
                    # name=form.name.data,
                    # contact_info=form.contact_info.data
                    )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))  # Redirect to login page after registration
    return render_template('auth/register.html', title='Register', form=form)