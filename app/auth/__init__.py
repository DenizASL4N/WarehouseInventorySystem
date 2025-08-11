# app/auth/__init__.py
from flask import Blueprint

# 'auth' adında bir Blueprint örneği oluşturuyoruz.
# İlk argüman Blueprint'in adı, ikincisi __name__ (modülün veya paketin adı),
# üçüncüsü ise bu Blueprint'e ait şablonların (template) bulunacağı klasör.
bp = Blueprint('auth', __name__, template_folder='templates')

# Bu Blueprint'e ait route'ları (ve view fonksiyonlarını) import ediyoruz.
# Bu import, bp nesnesi tanımlandıktan sonra yapılmalı ki döngüsel import olmasın.
from app.auth import routes