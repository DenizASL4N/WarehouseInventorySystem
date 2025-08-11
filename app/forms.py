# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DecimalField, DateField, \
    IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from app.models import User

USER_ROLE_CHOICES = [
    ('Admin', 'Administrator'),
    ('WarehouseManager', 'Warehouse Manager'),
    ('InventoryStaff', 'Inventory Staff'),
    ('SalesTeam', 'Sales Team')
]


class LoginForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(message="Username field cannot be empty."),
                                       Length(min=3, max=64, message="Username must be between 3 and 64 characters.")])
    password = PasswordField('Password',
                             validators=[DataRequired(message="Password field cannot be empty.")])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(message="Username field cannot be empty."),
                                       Length(min=3, max=64, message="Username must be between 3 and 64 characters.")])
    email = StringField('Email Address',
                        validators=[DataRequired(message="Email field cannot be empty."),
                                    Email(message="Please enter a valid email address."),
                                    Length(max=120, message="Email address can be at most 120 characters.")])
    password = PasswordField('Password',
                             validators=[DataRequired(message="Password field cannot be empty."),
                                         Length(min=6, message="Password must be at least 6 characters long.")])
    password2 = PasswordField('Repeat Password',
                              validators=[DataRequired(message="Repeat password field cannot be empty."),
                                          EqualTo('password', message="Passwords must match.")])
    submit = SubmitField('Register')

    def validate_username(self, username_field):
        user = User.query.filter_by(username=username_field.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')

    def validate_email(self, email_field):
        user = User.query.filter_by(email=email_field.data).first()
        if user:
            raise ValidationError('This email address is already registered. Please choose a different one.')


class ProductForm(FlaskForm):
    name = StringField('Product Name',
                       validators=[DataRequired(message="Product name is required."),
                                   Length(min=2, max=100,
                                          message="Product name must be between 2 and 100 characters.")])
    category = StringField('Category',
                           validators=[Optional(),
                                       Length(max=50, message="Category can be at most 50 characters.")])
    quantity_in_stock = IntegerField('Quantity in Stock',
                                     validators=[DataRequired(message="Stock quantity is required."),
                                                 NumberRange(min=0, message="Stock quantity must be 0 or greater.")])
    price = DecimalField('Selling Price ($)',
                         validators=[DataRequired(message="Price is required."),
                                     NumberRange(min=0.01, message="Price must be greater than 0.")],
                         places=2)
    expiry_date = DateField('Expiry Date (YYYY-MM-DD)',
                            format='%Y-%m-%d',
                            validators=[Optional()])
    description = TextAreaField('Description',
                                validators=[Optional(),
                                            Length(max=500, message="Description can be at most 500 characters.")])
    supplier_id = SelectField('Supplier', coerce=int, validators=[Optional()])
    warehouse_id = SelectField('Warehouse Location', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Product')


class SupplierForm(FlaskForm):
    name = StringField('Supplier Name',
                       validators=[DataRequired(message="Supplier name is required."),
                                   Length(min=2, max=100,
                                          message="Supplier name must be between 2 and 100 characters.")])
    contact_name = StringField('Contact Person',
                               validators=[Optional(),
                                           Length(max=100,
                                                  message="Contact person name can be at most 100 characters.")])
    contact_email = StringField('Contact Email',
                                validators=[Optional(), Email(message="Please enter a valid email address."),
                                            Length(max=120)])
    contact_phone = StringField('Contact Phone',
                                validators=[Optional(), Length(max=50)])
    address = TextAreaField('Address',
                            validators=[Optional(),
                                        Length(max=255, message="Address can be at most 255 characters.")])
    submit = SubmitField('Save Supplier')


class WarehouseLocationForm(FlaskForm):
    name = StringField('Warehouse Name',
                       validators=[Optional(),
                                   Length(max=100, message="Warehouse name can be at most 100 characters.")])
    address = StringField('Address',
                          validators=[DataRequired(message="Address is required."),
                                      Length(min=5, max=255, message="Address must be between 5 and 255 characters.")])
    capacity = IntegerField('Capacity (e.g., number of pallets, m²)',
                            validators=[Optional(),
                                        NumberRange(min=0, message="Capacity must be a non-negative number.")])
    submit = SubmitField('Save Warehouse Location')


class AdminUserForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(message="Username is required."),
                                       Length(min=3, max=64)])
    email = StringField('Email Address',
                        validators=[DataRequired(message="Email is required."),
                                    Email(), Length(max=120)])
    password = PasswordField('Password (leave blank to keep current)',
                             validators=[Optional(),
                                         Length(min=6, message="Password must be at least 6 characters.")])
    password2 = PasswordField('Repeat Password',
                              validators=[EqualTo('password', message="Passwords must match.")])
    name = StringField('Full Name', validators=[Optional(), Length(max=100)])
    contact_info = StringField('Contact Info', validators=[Optional(), Length(max=100)])
    role = SelectField('Role', choices=USER_ROLE_CHOICES,
                       validators=[DataRequired(message="Role is required.")])
    is_active = BooleanField('Active User', default=True)
    submit = SubmitField('Save User')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(AdminUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username_field):
        if username_field.data != self.original_username:
            user = User.query.filter_by(username=username_field.data).first()
            if user:
                raise ValidationError('This username is already taken.')

    def validate_email(self, email_field):
        if email_field.data != self.original_email:
            user = User.query.filter_by(email=email_field.data).first()
            if user:
                raise ValidationError('This email address is already registered.')

    def validate_password(self, password_field):
        # This validator is tricky with 'Optional' and edit forms.
        # It's better to handle password requirement logic in the route for 'add_user'.
        # If password has data, then password2 should also have data (handled by EqualTo).
        if self.password.data and not self.password2.data:
            # EqualTo validator should catch this if password2 is also DataRequired conditionally
            # Forcing password2 to be required if password is set
            if 'DataRequired' not in [v.__class__ for v in self.password2.validators]:
                # This is a bit hacky, ideally this logic is in the route or a more complex form setup
                pass  # Let EqualTo handle it or make password2 DataRequired in route if password has data.
        pass


class EmptyForm(FlaskForm):
    pass