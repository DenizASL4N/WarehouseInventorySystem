# app/models.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login  # app/__init__.py'den db ve login nesnelerini import et


# User sınıfının tanımını @login.user_loader'dan ÖNCEYE alıyoruz
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    contact_info = db.Column(db.String(100), nullable=True)

    # UserMixin ile çakışmayı önlemek için veritabanı sütununun Python'daki adı _is_active,
    # ama veritabanındaki gerçek sütun adı 'is_active' olarak kalacak.
    # default=True ve nullable=False, yeni sütun eklenirken MS SQL Server'ın sorun çıkarmamasına yardımcı olur.
    _is_active = db.Column(db.Boolean, default=True, nullable=False, name='is_active')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders_placed = db.relationship('Order', backref='customer', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login'in UserMixin'inin beklediği is_active özelliği
    @property
    def is_active(self):
        return self._is_active

    # is_active özelliğine değer atamak için setter metodu
    @is_active.setter
    def is_active(self, value):
        self._is_active = bool(value)

    def __repr__(self):
        return f'<User {self.username} (Role: {self.role})>'


# Flask-Login'in kullanıcıyı yükleyebilmesi için bu fonksiyon gerekli
@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    contact = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products_supplied = db.relationship('Product', backref='supplier_details', lazy='dynamic')

    def __repr__(self):
        return f'<Supplier {self.name}>'


class WarehouseLocation(db.Model):
    __tablename__ = 'warehouse_locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=True, index=True)
    address = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products_stored = db.relationship('Product', backref='storage_location', lazy='dynamic')

    def __repr__(self):
        return f'<WarehouseLocation {self.name if self.name else self.address}>'


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=True)
    quantity_in_stock = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Selling Price
    expiry_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    purchase_price = db.Column(db.Numeric(10, 2), nullable=True)  # Cost/Purchase Price
    low_stock_threshold = db.Column(db.Integer, default=10, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse_locations.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)

    order_items = db.relationship('OrderItem', backref='product_details', lazy='dynamic')

    def __repr__(self):
        return f'<Product {self.name}>'


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, index=True, nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False, default='Pending', index=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    items = db.relationship('OrderItem', backref='order_ref', lazy='dynamic', cascade="all, delete-orphan")

    def calculate_and_set_total(self):
        total = sum(item.quantity * item.price_at_order for item in self.items)
        self.total_amount = total

    def __repr__(self):
        return f'<Order #{self.order_number} - User: {self.customer.username if self.customer else "N/A"} - Status: {self.status}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_order = db.Column(db.Numeric(10, 2), nullable=False)

    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    def get_item_total(self):
        return self.quantity * self.price_at_order

    def __repr__(self):
        return f'<OrderItem OrderID: {self.order_id} ProductID: {self.product_id} Qty: {self.quantity}>'