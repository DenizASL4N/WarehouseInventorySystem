# app/admin/__init__.py
from flask import Blueprint

# 'admin' adında bir Blueprint örneği oluşturuyoruz.
# template_folder='templates' -> Bu blueprint'e ait şablonlar app/admin/templates/admin/ içinde olacak.
# url_prefix='/admin' -> Bu blueprint'teki tüm route'lar /admin/ ile başlayacak.
bp = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')

# Bu Blueprint'e ait route'ları (ve view fonksiyonlarını) import ediyoruz.
# Bu import, bp nesnesi tanımlandıktan sonra yapılmalı ki döngüsel import olmasın.
from app.admin import routes