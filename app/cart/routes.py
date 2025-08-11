# app/cart/routes.py
from flask import render_template, redirect, url_for, flash, request, session, abort
from flask_login import login_required
from app import db
from app.cart import bp
from app.models import Product


@bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = db.session.get(Product, product_id) or abort(404)
    quantity = int(request.form.get('quantity', 1))  # Formdan miktar al, varsayılan 1

    if quantity <= 0:
        flash('Quantity must be at least 1.', 'warning')
        return redirect(request.referrer or url_for('products.list_products'))

    # Initialize cart in session if it doesn't exist
    if 'cart' not in session:
        session['cart'] = {}  # item_id: {'name': ..., 'price': ..., 'quantity': ...}

    cart = session['cart']
    str_product_id = str(product_id)  # Session anahtarları string olmalı

    if str_product_id in cart:
        # Ürün zaten sepetteyse, miktarı artır (stok kontrolü eklenebilir)
        if product.quantity_in_stock >= cart[str_product_id]['quantity'] + quantity:
            cart[str_product_id]['quantity'] += quantity
            flash(f'{quantity} more of "{product.name}" added to your cart.', 'success')
        else:
            flash(
                f'Not enough stock for "{product.name}". Only {product.quantity_in_stock - cart[str_product_id]["quantity"]} more available.',
                'warning')
    else:
        # Ürünü sepete yeni ekle (stok kontrolü eklenebilir)
        if product.quantity_in_stock >= quantity:
            cart[str_product_id] = {
                'name': product.name,
                'price': float(product.price),  # Decimal'i float'a çevir (session için)
                'quantity': quantity,
                'image_filename': None  # Eğer ürün resmi varsa eklenebilir
            }
            flash(f'"{product.name}" added to your cart.', 'success')
        else:
            flash(f'Not enough stock to add "{product.name}". Only {product.quantity_in_stock} available.', 'warning')

    session.modified = True  # Session'da değişiklik yapıldığını belirt
    return redirect(request.referrer or url_for('products.list_products'))  # Önceki sayfaya veya ürün listesine dön


@bp.route('/')  # /cart/
@login_required
def view_cart():
    cart_items = session.get('cart', {})
    total_cart_amount = 0
    processed_cart = []  # Şablona göndermek için işlenmiş sepet listesi

    for item_id, item_data in cart_items.items():
        subtotal = item_data['quantity'] * item_data['price']
        total_cart_amount += subtotal
        processed_cart.append({
            'id': item_id,
            'name': item_data['name'],
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'subtotal': subtotal
        })

    return render_template('cart/view_cart.html',
                           title='Your Shopping Cart',
                           cart=processed_cart,
                           total_cart_amount=total_cart_amount)


@bp.route('/update/<product_id>', methods=['POST'])
@login_required
def update_cart_item(product_id):
    cart = session.get('cart', {})
    str_product_id = str(product_id)
    quantity = int(request.form.get('quantity', 0))

    if str_product_id in cart:
        product = db.session.get(Product, int(product_id))  # Stok kontrolü için
        if quantity > 0:
            if product and product.quantity_in_stock >= quantity:
                cart[str_product_id]['quantity'] = quantity
                flash('Cart updated.', 'success')
            elif product:
                flash(f'Not enough stock for "{product.name}". Only {product.quantity_in_stock} available.', 'warning')
                # Miktarı mevcut stoğa ayarla
                cart[str_product_id]['quantity'] = product.quantity_in_stock if product.quantity_in_stock > 0 else 0
                if cart[str_product_id]['quantity'] == 0 and product.quantity_in_stock == 0:
                    del cart[str_product_id]  # Stok yoksa ve 0 isteniyorsa sil
            else:  # Ürün bulunamadı (pek olası değil ama)
                del cart[str_product_id]
                flash('Product not found and removed from cart.', 'warning')

        else:  # quantity <= 0 ise ürünü sepetten çıkar
            del cart[str_product_id]
            flash('Item removed from cart.', 'info')
        session.modified = True
    return redirect(url_for('cart.view_cart'))


@bp.route('/remove/<product_id>', methods=['POST'])  # Veya GET ile de yapılabilir ama POST daha güvenli
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    str_product_id = str(product_id)
    if str_product_id in cart:
        del cart[str_product_id]
        session.modified = True
        flash('Item removed from cart.', 'info')
    return redirect(url_for('cart.view_cart'))


@bp.route('/clear')
@login_required
def clear_cart():
    session.pop('cart', None)  # Sepeti session'dan sil
    flash('Your cart has been cleared.', 'info')
    return redirect(url_for('products.list_products'))