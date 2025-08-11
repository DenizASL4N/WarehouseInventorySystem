# Warehouse Inventory System

This project is a comprehensive warehouse inventory management system developed using the Python Flask framework. It includes various modules such as inventory management, product tracking, order management, user authentication, and reporting.

## Features

* **Product Management:** Add, delete, update, and list products.
* **Warehouse Management:** Create and manage different warehouses.
* **Supplier Management:** Manage supplier information.
* **Order Management:** Create and track customer orders.
* **User Authentication:** Secure user login and authentication (`auth` module).
* **Shopping Cart Functionality:** Add products from inventory and create orders (`cart` module).
* **Database Management:** Database schema management using `Flask-SQLAlchemy` and `alembic`.

## Requirements

The project uses the following Python libraries. The `requirements.txt` file can be used for installation.

* `alembic==1.15.2`
* `blinker==1.9.0`
* `Flask==3.1.1`
* `Flask-Login==0.6.3`
* `Flask-Migrate==4.1.0`
* `Flask-SQLAlchemy==3.1.1`
* `SQLAlchemy==2.0.41`
* `mysql-connector-python==9.3.0`
* `pyodbc==5.2.0`
* ... and other dependencies

## Installation and Usage

1.  **Clone the Project:**
    ```bash
    git clone [https://github.com/SadikBoraErteni/WarehouseInventorySystem.git](https://github.com/SadikBoraErteni/WarehouseInventorySystem.git)
    cd WarehouseInventorySystem
    ```
2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    ```
3.  **Activate the Virtual Environment:**
    * **Windows:** `venv\Scripts\activate`
    * **macOS / Linux:** `source venv/bin/activate`
4.  **Install Required Libraries:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Prepare the Database:**
    Update the database settings in the `config.py` file with your own database connection details and create the database schema.
6.  **Run the Project:**
    ```bash
    python run.py
    ```

## Project Structure

The project has a modular design following Flask's blueprint structure:
* `admin/`
* `auth/`
* `cart/`
* `main/`
* `orders/`
* `products/`
* `suppliers/`
* `warehouses/`
* `templates/`

Additionally, core project files such as `run.py`, `requirements.txt`, and `config.py` are located in the root directory.
