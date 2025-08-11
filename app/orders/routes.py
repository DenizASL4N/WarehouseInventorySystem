# app/orders/routes.py
from flask import render_template, redirect, url_for, flash, session, abort, request, current_app
from flask_login import login_required, current_user
from app import db
from app.orders import bp
from app.models import Product, Order, OrderItem, User
# from app.forms import OrderForm # Henüz OrderForm kullanmıyoruz

import uuid  # For unique order numbers
import traceback  # For detailed error logging


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_order():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty. Please add products to your cart before creating an order.', 'warning')
        return redirect(url_for('products.list_products'))

    if request.method == 'POST':
        try:
            new_order = Order(
                order_number=str(uuid.uuid4()).split('-')[0].upper(),
                user_id=current_user.id,
                status='Pending'
                # shipping_address=form.shipping_address.data (if using OrderForm)
                # notes=form.notes.data (if using OrderForm)
            )

            total_order_amount = 0.0
            items_to_process = []  # To store product and quantity for stock update after checks

            # First pass: Check stock and gather items
            for product_id_str, item_data in cart.items():
                product_id = int(product_id_str)
                product = db.session.get(Product, product_id)

                if not product:
                    flash(
                        f"Product '{item_data.get('name', 'Unknown')}' (ID: {product_id}) could not be found. Order creation failed.",
                        "danger")
                    # No rollback here yet, just redirect
                    return redirect(url_for('cart.view_cart'))

                quantity_ordered = int(item_data['quantity'])  # Ensure quantity is int
                price_at_order = float(item_data['price'])  # Ensure price is float

                if product.quantity_in_stock < quantity_ordered:
                    flash(
                        f'Not enough stock for "{product.name}". Only {product.quantity_in_stock} available. Please update your cart. Order creation failed.',
                        'danger')
                    return redirect(url_for('cart.view_cart'))

                items_to_process.append({
                    'product_obj': product,  # Store the actual product object
                    'quantity': quantity_ordered,
                    'price_at_order': price_at_order
                })
                total_order_amount += quantity_ordered * price_at_order

            if not items_to_process:  # Should not happen if cart was not empty and no errors above
                flash('No valid items to process for the order.', 'warning')
                return redirect(url_for('cart.view_cart'))

            # If all checks passed, proceed to create order and items, and update stock
            new_order.total_amount = total_order_amount
            db.session.add(new_order)  # Add order to session first

            for item_info in items_to_process:
                order_item = OrderItem(
                    # DÜZELTİLMİŞ KISIM: Doğru backref isimlerini kullan
                    order_ref=new_order,  # Corresponds to backref in Order.items
                    product_details=item_info['product_obj'],  # Corresponds to backref in Product.order_items
                    quantity=item_info['quantity'],
                    price_at_order=item_info['price_at_order']
                )
                # Adding order_item to new_order.items collection is usually handled by SQLAlchemy
                # when new_order is added to session, due to the relationship and cascade settings.
                # Explicitly adding can be done if needed: db.session.add(order_item)
                # Or append to the collection if that's preferred for clarity:
                new_order.items.append(order_item)  # This also stages order_item for addition

                # Update stock
                item_info['product_obj'].quantity_in_stock -= item_info['quantity']

            db.session.commit()  # Commit all changes: new order, new order_items, updated product stocks

            # Clear the cart from session
            session.pop('cart', None)
            session.modified = True

            flash(f'Your order #{new_order.order_number} has been placed successfully!', 'success')
            return redirect(url_for('orders.order_detail', order_id=new_order.id))

        except Exception as e:
            db.session.rollback()  # Rollback in case of any error during the process
            current_app.logger.error(f"Order creation error: {e}\n{traceback.format_exc()}")
            flash(f'An error occurred while placing your order. Please try again or contact support. Error: {str(e)}',
                  'danger')
            return redirect(url_for('cart.view_cart'))

    # GET request: Show order confirmation/summary page
    cart_items_processed = []
    current_total_amount = 0.0
    if cart:  # Ensure cart exists
        for item_id_str, item_data in cart.items():
            # Ensure price and quantity are numbers for calculation
            price = float(item_data.get('price', 0))
            quantity = int(item_data.get('quantity', 0))
            subtotal = quantity * price
            current_total_amount += subtotal
            cart_items_processed.append({
                'id': item_id_str,
                'name': item_data.get('name', 'N/A'),
                'price': price,
                'quantity': quantity,
                'subtotal': subtotal
            })

    return render_template('orders/create_order.html',
                           title='Confirm Your Order',
                           cart_items=cart_items_processed,
                           current_total_amount=current_total_amount)


@bp.route('/')
@login_required
def list_orders():
    page = request.args.get('page', 1, type=int)
    # Assuming Admin role can see all orders, others see their own.
    # Modify this logic based on your actual role names and requirements.
    if current_user.role == 'Admin':  # Replace 'Admin' with your actual admin role name
        query = Order.query
    else:
        query = Order.query.filter_by(user_id=current_user.id)

    orders_pagination = query.order_by(Order.order_date.desc()) \
        .paginate(page=page, per_page=10, error_out=False)
    orders_items = orders_pagination.items
    return render_template('orders/list_orders.html',
                           title='My Orders' if current_user.role != 'Admin' else 'All Orders',
                           orders=orders_items,
                           pagination=orders_pagination)


@bp.route('/<int:order_id>')
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    # Allow user to see their own order, or admin to see any order
    if order.user_id != current_user.id and current_user.role != 'Admin':  # Replace 'Admin'
        abort(403)  # Forbidden
    return render_template('orders/order_detail.html', title=f'Order #{order.order_number}', order=order)