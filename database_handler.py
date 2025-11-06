import mysql.connector
from mysql.connector import Error, DatabaseError
from datetime import datetime
import time
from config import DB_CONFIG

class DatabaseHandler:
    def __init__(self):
        self.connection = None
        self.is_connected = False
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 2
        
    def init_database(self):
        """Initialize database connection dengan error handling yang lebih baik"""
        try:
            print("   🔌 Menghubungkan ke database MySQL Server...")
            print(f"   📍 Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
            print(f"   📊 Database: {DB_CONFIG['database']}")
            
            # Tambahkan parameter koneksi tambahan
            config = DB_CONFIG.copy()
            config.update({
                'connection_timeout': 10,
                'buffered': True,
                'autocommit': True,
                'pool_size': 5,
                'pool_name': 'face_recognition_pool'
            })
            
            self.connection = mysql.connector.connect(**config)
            self.is_connected = True
            self.retry_count = 0
            
            # Test connection dengan query yang lebih meaningful
            cursor = self.connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            cursor.execute("SELECT NOW()")
            server_time = cursor.fetchone()
            cursor.close()
            
            print(f"   ✅ Database berhasil diinisialisasi")
            print(f"   🗄️  MySQL Version: {version[0]}")
            print(f"   ⏰ Server Time: {server_time[0]}")
            return True
            
        except Error as e:
            self.retry_count += 1
            error_msg = str(e)
            print(f"   ❌ Database connection failed (Attempt {self.retry_count}): {e}")
            
            # Berikan solusi spesifik berdasarkan error
            if "Access denied" in error_msg:
                print("   💡 Username/Password MySQL salah! Periksa config.py")
                print(f"   💡 Current user: {DB_CONFIG['user']}")
            elif "Unknown database" in error_msg:
                print(f"   💡 Database '{DB_CONFIG['database']}' belum ada!")
                print("   💡 Jalankan: python database_setup.py")
            elif "Can't connect" in error_msg:
                print("   💡 MySQL server tidak berjalan atau tidak bisa diakses!")
                print(f"   💡 Host: {DB_CONFIG['host']}, Port: {DB_CONFIG['port']}")
                print("   💡 Windows: net start mysql")
                print("   💡 Linux: sudo service mysql start")
                print("   💡 Docker: docker start mysql-container")
            elif "Connection timed out" in error_msg:
                print("   💡 Koneksi timeout. Periksa jaringan atau firewall.")
            else:
                print("   💡 Periksa koneksi MySQL server dan konfigurasi")
                
            self.is_connected = False
            
            # Auto-retry mechanism
            if self.retry_count < self.max_retries:
                print(f"   🔄 Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                return self.init_database()
            else:
                print("   💥 Maximum retry attempts reached. Giving up.")
                return False
    
    def ensure_connection(self):
        """Memastikan koneksi database masih aktif"""
        if not self.is_connected or self.connection is None:
            return self.init_database()
        
        try:
            # Check if connection is still alive
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Error:
            print("   🔄 Connection lost, attempting to reconnect...")
            self.is_connected = False
            return self.init_database()
    
    def save_log(self, consistent_id, name, status):
        """Save face recognition log to database dengan transaction handling"""
        if not self.ensure_connection():
            return False
            
        cursor = None
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO logs (consistent_id, nim_nama, status_masuk_keluar, waktu) 
                VALUES (%s, %s, %s, %s)
            """
            values = (str(consistent_id), name, status, datetime.now())
            cursor.execute(query, values)
            self.connection.commit()
            
            print(f"   📝 Log saved: {name} - {status}")
            return True
            
        except Error as e:
            print(f"   ❌ [DATABASE ERROR] Failed to save log: {e}")
            # Rollback in case of error
            try:
                self.connection.rollback()
            except:
                pass
            
            # Try to reconnect and retry once
            if "MySQL Connection not available" in str(e):
                self.is_connected = False
                if self.ensure_connection():
                    return self.save_log(consistent_id, name, status)
            return False
            
        finally:
            if cursor:
                cursor.close()
    
    def update_statistics(self, total_masuk, total_keluar, wajah_di_dalam, unique_faces):
        """Update statistics table dengan error handling"""
        if not self.ensure_connection():
            return False
            
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            # First, check if statistics table has data
            cursor.execute("SELECT COUNT(*) as count FROM statistics")
            result = cursor.fetchone()
            
            if result[0] == 0:
                # Insert new record if doesn't exist
                query = """
                    INSERT INTO statistics 
                    (total_masuk, total_keluar, wajah_di_dalam, unique_faces, last_updated) 
                    VALUES (%s, %s, %s, %s, %s)
                """
                values = (total_masuk, total_keluar, wajah_di_dalam, unique_faces, datetime.now())
            else:
                # Update existing record
                query = """
                    UPDATE statistics 
                    SET total_masuk = %s, total_keluar = %s, wajah_di_dalam = %s, 
                        unique_faces = %s, last_updated = %s
                    WHERE id = 1
                """
                values = (total_masuk, total_keluar, wajah_di_dalam, unique_faces, datetime.now())
                
            cursor.execute(query, values)
            self.connection.commit()
            
            print(f"   📊 Statistics updated: Masuk={total_masuk}, Keluar={total_keluar}, Inside={wajah_di_dalam}, Unique={unique_faces}")
            return True
            
        except Error as e:
            print(f"   ❌ [DATABASE ERROR] Failed to update statistics: {e}")
            try:
                self.connection.rollback()
            except:
                pass
            return False
            
        finally:
            if cursor:
                cursor.close()
    
    def get_current_statistics(self):
        """Mengambil data statistics saat ini"""
        if not self.ensure_connection():
            return None
            
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM statistics WHERE id = 1")
            result = cursor.fetchone()
            return result
            
        except Error as e:
            print(f"   ❌ [DATABASE ERROR] Failed to get statistics: {e}")
            return None
            
        finally:
            if cursor:
                cursor.close()
    
    def get_recent_logs(self, limit=10):
        """Mengambil logs terbaru"""
        if not self.ensure_connection():
            return []
            
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM logs 
                ORDER BY waktu DESC 
                LIMIT %s
            """, (limit,))
            result = cursor.fetchall()
            return result
            
        except Error as e:
            print(f"   ❌ [DATABASE ERROR] Failed to get recent logs: {e}")
            return []
            
        finally:
            if cursor:
                cursor.close()
    
    def test_connection(self):
        """Test koneksi database"""
        try:
            if self.ensure_connection():
                cursor = self.connection.cursor()
                cursor.execute("SELECT DATABASE(), USER(), NOW()")
                result = cursor.fetchone()
                cursor.close()
                print(f"   ✅ Connection test successful")
                print(f"   📋 Database: {result[0]}, User: {result[1]}, Time: {result[2]}")
                return True
            return False
        except Error as e:
            print(f"   ❌ Connection test failed: {e}")
            return False
    
    def close_connection(self):
        """Menutup koneksi database dengan aman"""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                self.is_connected = False
                print("   🔌 Database connection closed")
        except Error as e:
            print(f"   ❌ Error closing connection: {e}")
    
    def __del__(self):
        """Cleanup connection"""
        self.close_connection()