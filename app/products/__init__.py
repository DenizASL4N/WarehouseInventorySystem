# app/products/__init__.py
from flask import Blueprint

# 'products' adında bir Blueprint örneği oluşturuyoruz.
# template_folder='templates' -> Bu blueprint'e ait şablonlar app/products/templates/ içinde olacak.
# url_prefix='/products' -> Bu blueprint'teki tüm route'lar /products/ ile başlayacak.
bp = Blueprint('products', __name__, template_folder='templates', url_prefix='/products')

# Bu Blueprint'e ait route'ları (ve view fonksiyonlarını) import ediyoruz.
from app.products import routes