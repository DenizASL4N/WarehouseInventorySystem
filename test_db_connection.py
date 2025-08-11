import pyodbc
import os
from dotenv import load_dotenv

# .env dosyasını yükle (eğer test_db_connection.py proje kökündeyse)
# Eğer farklı bir yerdeyse, .env dosyasının yolunu doğru verin
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(".env dosyası bulunamadı! Lütfen yolunu kontrol edin veya manuel olarak DATABASE_URL'i girin.")
    exit()

# .env dosyasından DATABASE_URL'i al
# ÖNEMLİ: Flask-SQLAlchemy'nin 'mssql+pyodbc://' önekini burada kullanmayacağız.
# Sadece pyodbc'nin anlayacağı formatta olmalı.
# Örnek: DRIVER={ODBC Driver 17 for SQL Server};SERVER=SUNUCU_ADINIZ;DATABASE=VERITABANI_ADINIZ;Trusted_Connection=yes;

# .env dosyasındaki DATABASE_URL'den pyodbc için uygun connection string'i çıkaralım
db_url_env = os.environ.get('DATABASE_URL')

if not db_url_env:
    print("DATABASE_URL ortam değişkeni .env dosyasında bulunamadı.")
    exit()

# Flask-SQLAlchemy önekini ('mssql+pyodbc://@') kaldıralım
# ve parametreleri ayıralım
if db_url_env.startswith('mssql+pyodbc://@'):
    params_str = db_url_env.split('@', 1)[1]  # SUNUCU_ADINIZ/VERITABANI_ADINIZ?driver=...&trusted_connection=yes

    # Sunucu ve Veritabanı adını al
    server_and_db, query_params = params_str.split('?', 1)
    server_name, database_name = server_and_db.split('/', 1)

    # Query parametrelerini parse et
    conn_params = {}
    for param in query_params.split('&'):
        key, value = param.split('=', 1)
        conn_params[key.lower()] = value.replace('+', ' ')  # '+' karakterlerini boşlukla değiştir

    driver = conn_params.get('driver', 'ODBC Driver 17 for SQL Server')  # Varsayılan sürücü
    trusted_connection = conn_params.get('trusted_connection', 'no')

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server_name};"
        f"DATABASE={database_name};"
        f"Trusted_Connection={trusted_connection};"
    )
    print(f"Oluşturulan Bağlantı Dizesi (pyodbc için): {conn_str}")
else:
    print(f"DATABASE_URL formatı beklenenden farklı: {db_url_env}")
    print("Lütfen .env dosyasındaki DATABASE_URL'i kontrol edin.")
    print(
        "Beklenen format: 'mssql+pyodbc://@SUNUCU_ADINIZ/VERITABANI_ADINIZ?driver=DRIVER_ADINIZ&trusted_connection=yes'")
    exit()

try:
    # Veritabanına bağlanmayı dene
    conn = pyodbc.connect(conn_str)
    print("MS SQL Server'a başarıyla bağlanıldı! (Windows Authentication)")

    # Bağlantıyı test etmek için basit bir sorgu çalıştır (opsiyonel)
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION;")  # SQL Server versiyonunu getir
    row = cursor.fetchone()
    if row:
        print(f"SQL Server Versiyonu: {row[0]}")

    cursor.close()
    conn.close()
    print("Bağlantı başarıyla kapatıldı.")

except pyodbc.Error as ex:
    sqlstate = ex.args[0]
    print(f"MS SQL Server'a bağlanırken hata oluştu: {sqlstate}")
    print(f"Hata Detayı: {ex}")
    if 'Login failed' in str(ex):
        print(
            "Giriş başarısız oldu. Lütfen SQL Server'daki Windows kullanıcınızın yetkilerini ve sunucu adını kontrol edin.")
    elif 'Server does not exist or access denied' in str(ex):
        print("Sunucu bulunamadı veya erişim engellendi. Lütfen sunucu adını ve ağ bağlantınızı kontrol edin.")
    elif 'Driver' in str(ex) and 'not found' in str(ex):
        print(
            f"Belirtilen ODBC sürücüsü ({driver}) bulunamadı. Lütfen ODBC sürücülerinizin kurulu olduğundan emin olun.")
    else:
        print("Bağlantı dizesini ve veritabanı sunucusunun çalıştığını kontrol edin.")
        print(f"Kullanılan bağlantı dizesi: {conn_str}")

except Exception as e:
    print(f"Beklenmedik bir hata oluştu: {e}")