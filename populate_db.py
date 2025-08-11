import random
from datetime import datetime, timedelta
from faker import Faker
import uuid
from app import create_app, db
from app.models import User, Supplier, WarehouseLocation, Product, Order, OrderItem

# from sqlalchemy import func # Eğer func.random() gibi şeyler kullanıyorsanız

app = create_app()
app.app_context().push()

fake = Faker()


# --- Yardımcı Fonksiyonlar (Aynı) ---
def get_random_user():
    users = User.query.all()
    return random.choice(users) if users else None


def get_random_product(only_in_stock=False):
    query = Product.query
    if only_in_stock:
        query = query.filter(Product.quantity_in_stock > 0)
    count = query.count()
    if count == 0: return None
    return query.offset(random.randint(0, count - 1)).first()


def get_random_supplier():
    count = Supplier.query.count()
    if count == 0: return None
    return Supplier.query.offset(random.randint(0, count - 1)).first()


def get_random_warehouse():
    count = WarehouseLocation.query.count()
    if count == 0: return None
    return WarehouseLocation.query.offset(random.randint(0, count - 1)).first()


# --- Veri Doldurma Fonksiyonları ---
def populate_users(count=50):
    print(f"Populating {count} users...")
    roles = ['Admin', 'WarehouseManager', 'InventoryStaff', 'SalesTeam']
    existing_usernames = {u.username for u in User.query.with_entities(User.username).all()}
    existing_emails = {u.email for u in User.query.with_entities(User.email).all()}
    users_to_add = []
    for i in range(count):
        username_candidate = f"{fake.user_name().replace('.', '_')}{i}"  # Noktaları alt çizgi ile değiştir
        while username_candidate in existing_usernames:
            username_candidate = f"{fake.user_name().replace('.', '_')}{i}{fake.lexify(text='??')}"
        existing_usernames.add(username_candidate)

        email_candidate = f"{username_candidate}@{fake.domain_name()}"
        while email_candidate in existing_emails:
            email_candidate = f"{username_candidate}{fake.lexify(text='??')}@{fake.domain_name()}"
        existing_emails.add(email_candidate)

        u = User(
            username=username_candidate, email=email_candidate,
            role=random.choice(roles), name=fake.name(),
            contact_info=fake.phone_number(), _is_active=True
        )
        u.set_password('password123')
        users_to_add.append(u)
    if users_to_add:
        db.session.add_all(users_to_add)
        try:
            db.session.commit()
            print(f"Successfully added {len(users_to_add)} users. Total users: {User.query.count()}.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding users: {e}")
            # raise e # Script'i durdurmak için hatayı tekrar fırlatabiliriz


def populate_suppliers(count=80):
    print(f"Populating {count} suppliers...")
    existing_names = {s.name for s in Supplier.query.with_entities(Supplier.name).all()}
    suppliers_to_add = []
    for i in range(count):
        name_candidate = f"{fake.company()} {fake.company_suffix()} {i}"
        while name_candidate in existing_names:
            name_candidate = f"{fake.company()} {fake.company_suffix()} {i}{fake.lexify(text='??')}"
        existing_names.add(name_candidate)
        s = Supplier(name=name_candidate, contact=fake.name(), address=fake.address().replace('\n', ', '))
        suppliers_to_add.append(s)
    if suppliers_to_add:
        db.session.add_all(suppliers_to_add)
        try:
            db.session.commit()
            print(f"Successfully added {len(suppliers_to_add)} suppliers. Total suppliers: {Supplier.query.count()}.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding suppliers: {e}")


def populate_warehouses(count=15):
    print(f"Populating {count} warehouses...")
    # Modelimizde name: unique=True, nullable=True; address: nullable=False, unique=True
    existing_names = {w.name for w in WarehouseLocation.query.with_entities(WarehouseLocation.name).filter(
        WarehouseLocation.name.isnot(None)).all()}
    existing_addresses = {w.address for w in WarehouseLocation.query.with_entities(WarehouseLocation.address).all()}
    warehouses_to_add = []

    for i in range(count):
        # İsim her zaman üretilecek ve benzersiz olacak
        name_candidate_base = f"Warehouse-{fake.city().replace(' ', '_')}-{random.randint(1000, 9999)}"
        name_candidate = f"{name_candidate_base}_v{i}"
        while name_candidate in existing_names:
            name_candidate = f"{name_candidate_base}_v{i}_{fake.lexify(text='?')}"
        existing_names.add(name_candidate)  # Üretilen ismi sete ekle

        # Adres her zaman üretilecek ve benzersiz olacak
        address_candidate_base = fake.address().replace('\n', ', ')
        address_candidate = f"{address_candidate_base} (Loc: {i})"
        while address_candidate in existing_addresses:
            address_candidate = f"{address_candidate_base} (Loc: {i}_{fake.lexify(text='?')})"
        existing_addresses.add(address_candidate)  # Üretilen adresi sete ekle

        capacity = random.choice([500, 1000, 2500, 5000, 10000])  # Daha belirgin kapasiteler

        wh = WarehouseLocation(
            name=name_candidate,  # Artık her zaman bir değere sahip ve benzersiz
            address=address_candidate,  # Artık her zaman bir değere sahip ve benzersiz
            capacity=capacity
        )
        warehouses_to_add.append(wh)

    if warehouses_to_add:
        db.session.add_all(warehouses_to_add)
        try:
            db.session.commit()
            print(
                f"Successfully added {len(warehouses_to_add)} warehouses. Total warehouses: {WarehouseLocation.query.count()}.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding warehouses: {e}")
            # raise e # Hatanın script'i durdurması için


def populate_products(count=1000):
    print(f"Populating {count} products...")
    categories = ['Electronics', 'Books', 'Clothing', 'Home Goods', 'Toys', 'Sports', 'Beauty', 'Groceries',
                  'Office Supplies', 'Automotive', 'Industrial', 'Garden', 'Software', 'Music']
    suppliers = Supplier.query.all()
    warehouses = WarehouseLocation.query.all()

    if not suppliers or not warehouses:
        print("Cannot populate products. Ensure suppliers and warehouses are populated first.")
        return

    products_to_add = []
    existing_names = {p.name for p in Product.query.with_entities(Product.name).all()}

    for i in range(count):
        name_candidate_base = f"{fake.bs().replace(' ', '-').capitalize()}-{random.choice(['Pro', 'Max', 'Lite', 'Ultra', 'Standard'])}"
        name_candidate = f"{name_candidate_base}-{random.randint(1000, 9999)}"
        loop_breaker = 0
        while name_candidate in existing_names and loop_breaker < 10:  # Sonsuz döngüden kaçın
            name_candidate = f"{name_candidate_base}-{random.randint(1000, 9999)}{fake.lexify(text='?')}"
            loop_breaker += 1
        if name_candidate in existing_names: continue  # Benzersiz bulunamadıysa atla
        existing_names.add(name_candidate)

        has_expiry_date = random.random() > 0.4  # %60 ihtimalle son kullanma tarihi olsun
        expiry_date_value = None
        if has_expiry_date:
            if random.random() < 0.10:  # %10 ihtimalle tarihi geçmiş olsun
                expiry_date_value = fake.date_between(start_date='-6m', end_date='-1d')
            else:
                expiry_date_value = fake.date_between(start_date='+1m', end_date='+2y')

        current_price = round(random.uniform(10.0, 2500.0), 2)
        purchase_p = None
        if random.random() > 0.15:  # %85 ihtimalle alış fiyatı olsun
            purchase_p = round(random.uniform(max(1.0, current_price * 0.2), current_price * 0.75), 2)

        selected_wh = random.choice(warehouses)
        quantity = 0
        if selected_wh.capacity and selected_wh.capacity > 0:
            # Depo kapasitesinin %0.1'i ile %5'i arasında rastgele bir miktar
            max_possible_stock_for_this_product = int(selected_wh.capacity * random.uniform(0.001, 0.05))
            quantity = random.randint(0, max(1, max_possible_stock_for_this_product))
        else:  # Kapasite tanımsızsa
            quantity = random.randint(0, 50)

        p = Product(
            name=name_candidate, category=random.choice(categories),
            quantity_in_stock=quantity, price=current_price,
            purchase_price=purchase_p, expiry_date=expiry_date_value,
            description=fake.sentence(nb_words=random.randint(10, 20)),
            low_stock_threshold=max(5, int(quantity * 0.25)) if quantity > 20 else 5,
            supplier_details=random.choice(suppliers), storage_location=selected_wh
        )
        products_to_add.append(p)

        if (i + 1) % 200 == 0 or i == count - 1:  # Her 200 üründe veya sonda commit et
            if products_to_add:  # Sadece eklenecek ürün varsa
                db.session.add_all(products_to_add)
                try:
                    db.session.commit()
                    print(f"Committed {len(products_to_add)} products. Total processed: {i + 1}/{count}.")
                    products_to_add = []
                except Exception as e:
                    db.session.rollback()
                    print(f"Error committing products batch ending at record {i + 1}: {e}")
                    products_to_add = []

    print(f"Product population finished. Total products in DB: {Product.query.count()}.")


def populate_orders_and_items(order_count=1500, items_per_order_range=(1, 4)):
    print(f"Populating {order_count} orders...")
    users = User.query.all()
    if not users: print("Cannot populate orders without users."); return

    all_products_list = Product.query.all()
    if not all_products_list: print("No products available to create orders."); return

    orders_batch_to_commit = []

    for i in range(order_count):
        customer = random.choice(users)
        order_date = fake.date_time_between(start_date='-2y', end_date='now')
        order_status = random.choice(['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned'])

        order_number_candidate = f"ORD-{str(uuid.uuid4()).split('-')[0].upper()}-{random.randint(10000, 99999)}"

        new_order = Order(order_number=order_number_candidate, order_date=order_date, status=order_status,
                          customer=customer)

        num_items_to_add = random.randint(items_per_order_range[0], items_per_order_range[1])
        order_total_amount = 0.0

        products_in_stock_for_this_order = [p for p in all_products_list if p.quantity_in_stock > 0]
        if not products_in_stock_for_this_order: continue

        selected_products = random.sample(
            products_in_stock_for_this_order,
            min(num_items_to_add, len(products_in_stock_for_this_order))
        )

        items_for_this_order = []
        stock_updates_for_this_order = []

        for product_obj in selected_products:
            if product_obj.quantity_in_stock <= 0: continue
            quantity_ordered = random.randint(1, min(3, product_obj.quantity_in_stock))

            price_at_order = float(product_obj.price)

            order_item = OrderItem(
                product_details=product_obj,
                quantity=quantity_ordered,
                price_at_order=price_at_order
            )
            items_for_this_order.append(order_item)
            order_total_amount += quantity_ordered * price_at_order
            stock_updates_for_this_order.append({'product_id': product_obj.id, 'ordered_qty': quantity_ordered})

        if not items_for_this_order: continue

        new_order.total_amount = round(order_total_amount, 2)
        new_order.items.extend(items_for_this_order)
        orders_batch_to_commit.append({'order': new_order, 'stock_updates': stock_updates_for_this_order})

        if (i + 1) % 50 == 0 or i == order_count - 1:  # Her 50 siparişte veya sonda commit et
            if orders_batch_to_commit:
                for entry in orders_batch_to_commit:
                    db.session.add(entry['order'])
                    for update_info in entry['stock_updates']:
                        prod_to_update = db.session.get(Product, update_info['product_id'])  # Session'dan al
                        if prod_to_update:
                            prod_to_update.quantity_in_stock -= update_info['ordered_qty']
                            if prod_to_update.quantity_in_stock < 0: prod_to_update.quantity_in_stock = 0
                try:
                    db.session.commit()
                    print(f"Committed {len(orders_batch_to_commit)} orders. Total processed: {i + 1}/{order_count}.")
                    orders_batch_to_commit = []
                except Exception as e:
                    db.session.rollback()
                    print(f"Error committing orders batch ending at record {i + 1}: {e}")
                    break
    print(f"Order population finished. Total orders in DB: {Order.query.count()}.")


if __name__ == '__main__':
    print("Deleting existing data (Users, Suppliers, Warehouses, Products, OrderItems, Orders)...")
    db.session.execute(db.text("DELETE FROM order_items"))
    db.session.execute(db.text("DELETE FROM orders"))
    db.session.execute(db.text("DELETE FROM products"))
    db.session.execute(db.text("DELETE FROM warehouse_locations"))
    db.session.execute(db.text("DELETE FROM suppliers"))
    db.session.execute(db.text("DELETE FROM users"))
    db.session.commit()
    print("Existing data deleted successfully.")

    populate_users(50)
    populate_suppliers(80)
    populate_warehouses(15)
    populate_products(1000)
    populate_orders_and_items(1500, items_per_order_range=(1, 4))

    print("-----------------------------------------")
    print(f"Total Users: {User.query.count()}")
    print(f"Total Suppliers: {Supplier.query.count()}")
    print(f"Total Warehouses: {WarehouseLocation.query.count()}")
    print(f"Total Products: {Product.query.count()}")
    print(f"Total Orders: {Order.query.count()}")
    print(f"Total Order Items: {OrderItem.query.count()}")
    print("Data population script finished.")