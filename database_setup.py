import mysql.connector
from config import DB_CONFIG

def setup_database():
    """Script untuk setup database dan tabel"""
    try:
        print("🔧 Memulai setup database...")
        
        # Connect tanpa database dulu
        config_temp = DB_CONFIG.copy()
        database_name = config_temp.pop('database')
        
        print("📡 Menghubungkan ke MySQL server...")
        conn = mysql.connector.connect(**config_temp)
        cursor = conn.cursor()
        
        # Buat database jika belum ada
        print("📦 Membuat database...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        cursor.execute(f"USE {database_name}")
        
        # Buat tabel logs
        print("📊 Membuat tabel logs...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                consistent_id VARCHAR(255) NOT NULL,
                nim_nama VARCHAR(255) NOT NULL,
                status_masuk_keluar ENUM('masuk', 'keluar') NOT NULL,
                waktu DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_consistent_id (consistent_id),
                INDEX idx_waktu (waktu)
            )
        """)
        
        # Buat tabel statistics
        print("📈 Membuat tabel statistics...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                total_masuk INT DEFAULT 0,
                total_keluar INT DEFAULT 0,
                wajah_di_dalam INT DEFAULT 0,
                unique_faces INT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Insert record statistics awal
        print("➕ Insert data awal statistics...")
        cursor.execute("""
            INSERT IGNORE INTO statistics (id, total_masuk, total_keluar, wajah_di_dalam, unique_faces) 
            VALUES (1, 0, 0, 0, 0)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database dan tabel berhasil dibuat!")
        print(f"📁 Database: {database_name}")
        print("📋 Tabel: logs, statistics")
        
    except mysql.connector.Error as e:
        print(f"❌ Error setup database: {e}")
        print("\n💡 SOLUSI:")
        print("1. Pastikan MySQL server berjalan")
        print("2. Windows: net start mysql")
        print("3. Linux: sudo service mysql start")
        print("4. Cek password di config.py")

if __name__ == "__main__":
    setup_database()