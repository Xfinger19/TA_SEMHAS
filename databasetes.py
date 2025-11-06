import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'saputra19',
    'database': 'wajah_yolov8_2',
    'port': 3306,
    'charset': 'utf8mb4'
}

try:
    connection = mysql.connector.connect(**DB_CONFIG)
    if connection.is_connected():
        print("✅ Berhasil terhubung ke MySQL database")
        
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        print(f"📊 Database yang digunakan: {db_name[0]}")
        
        # Test create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Test table berhasil dibuat")
        
except Error as e:
    print(f"❌ Error connecting to MySQL: {e}")
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("✅ Koneksi ditutup")