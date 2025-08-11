import os
from dotenv import load_dotenv

# Proje kök dizinini (config.py dosyasının bulunduğu dizin) bul
basedir = os.path.abspath(os.path.dirname(__file__))

# Proje kök dizinindeki .env dosyasını yükle
# Bu satır, .env dosyasının config.py ile aynı dizinde (proje kökünde) olduğunu varsayar.
env_path = os.path.join(basedir, '.env')
load_dotenv(dotenv_path=env_path)

class Config:
    """
    Flask uygulama yapılandırma ayarlarını içeren sınıf.
    Değerler öncelikle ortam değişkenlerinden (.env dosyasından) okunur,
    bulunamazsa varsayılan değerler atanabilir.
    """

    # Flask ve eklentileri için gizli anahtar. Üretimde MUTLAKA değiştirilmeli ve
    # .env dosyasından okunmalı.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cok-gizli-bir-varsayilan-anahtar-degistirin'

    # Veritabanı bağlantı dizesi
    # Bu değer .env dosyasındaki DATABASE_URL değişkeninden okunmalıdır.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Eğer .env dosyasında DATABASE_URL tanımlı değilse, bir uyarı verip
    # geliştirme için varsayılan bir SQLite veritabanına geçebiliriz (opsiyonel).
    # Ancak MS SQL Server kullanacağımız için .env dosyasında doğru şekilde tanımlanmış olması esastır.
    if not SQLALCHEMY_DATABASE_URI:
        print("UYARI: '.env' dosyasında 'DATABASE_URL' ortam değişkeni bulunamadı veya boş.")
        print("Lütfen .env dosyanızı ve MS SQL Server bağlantı dizenizi kontrol edin.")
        # Geliştirme kolaylığı için bir fallback tanımlanabilir, ama bu MS SQL projesi için pek mantıklı değil.
        # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app_fallback.db')


    # SQLAlchemy'nin olay sistemini devre dışı bırakır, performansı artırabilir.
    # Genellikle False olarak ayarlanması önerilir.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # İleride eklenebilecek diğer yapılandırma ayarları:
    # Örneğin: Mail sunucusu ayarları, dosya yükleme ayarları vb.
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMINS = ['your-email@example.com']