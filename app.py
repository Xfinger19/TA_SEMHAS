from flask import Flask, render_template, jsonify, request, send_from_directory
import mysql.connector
from datetime import datetime, timedelta
import json
import os
import sys

# Tambahkan path untuk import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG

app = Flask(__name__)

def get_db_connection():
    """Membuat koneksi ke database MySQL"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"[DATABASE ERROR] Gagal terkoneksi ke database: {e}")
        return None

def render_html(filename, **kwargs):
    """Render HTML file directly from root directory"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            html_content = file.read()
        from flask import render_template_string
        return render_template_string(html_content, **kwargs)
    except FileNotFoundError:
        return f"File {filename} tidak ditemukan", 404
    except Exception as e:
        return f"Error rendering template: {str(e)}", 500

# Route untuk file static (CSS, JS, images)
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files directly"""
    if os.path.isfile(filename):
        return send_from_directory('.', filename)
    return "File not found", 404

@app.route('/')
def index():
    """Halaman dashboard utama"""
    return render_html('index.html')

@app.route('/logs')
def logs():
    """Halaman menampilkan semua logs"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    if conn is None:
        return render_html('error.html', message="Koneksi database gagal"), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM logs")
        total = cursor.fetchone()['total']
        
        # Get logs dengan pagination
        cursor.execute("""
            SELECT * FROM logs 
            ORDER BY waktu DESC 
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        logs_data = cursor.fetchall()
        
        # Convert datetime objects to strings
        for log in logs_data:
            if isinstance(log['waktu'], datetime):
                log['waktu'] = log['waktu'].strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(log.get('created_at'), datetime):
                log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        total_pages = (total + per_page - 1) // per_page
        
        cursor.close()
        conn.close()
        
        return render_html('logs.html', 
                         logs=logs_data, 
                         page=page, 
                         total_pages=total_pages,
                         total=total)
    
    except mysql.connector.Error as e:
        print(f"[DATABASE ERROR] {e}")
        return render_html('error.html', message="Terjadi kesalahan database"), 500

@app.route('/statistics')
def statistics():
    """Halaman statistik lengkap"""
    conn = get_db_connection()
    if conn is None:
        return render_html('error.html', message="Koneksi database gagal"), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get current statistics
        cursor.execute("SELECT * FROM statistics ORDER BY last_updated DESC LIMIT 1")
        stats = cursor.fetchone()
        
        # Get today's activity
        today = datetime.now().date()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_activities,
                SUM(CASE WHEN status_masuk_keluar = 'masuk' THEN 1 ELSE 0 END) as masuk_today,
                SUM(CASE WHEN status_masuk_keluar = 'keluar' THEN 1 ELSE 0 END) as keluar_today
            FROM logs 
            WHERE DATE(waktu) = %s
        """, (today,))
        today_stats = cursor.fetchone()
        
        # Get unique faces today
        cursor.execute("""
            SELECT COUNT(DISTINCT consistent_id) as unique_faces_today
            FROM logs 
            WHERE DATE(waktu) = %s AND consistent_id IS NOT NULL
        """, (today,))
        unique_today = cursor.fetchone()
        
        # Get top active persons
        cursor.execute("""
            SELECT 
                nim_nama,
                COUNT(*) as activity_count,
                SUM(CASE WHEN status_masuk_keluar = 'masuk' THEN 1 ELSE 0 END) as masuk_count,
                SUM(CASE WHEN status_masuk_keluar = 'keluar' THEN 1 ELSE 0 END) as keluar_count
            FROM logs 
            WHERE nim_nama != 'Tidak Dikenali' AND nim_nama IS NOT NULL
            GROUP BY nim_nama 
            ORDER BY activity_count DESC 
            LIMIT 10
        """)
        top_persons = cursor.fetchall()
        
        # Get activity by hour for today
        cursor.execute("""
            SELECT 
                HOUR(waktu) as hour,
                COUNT(*) as count
            FROM logs 
            WHERE DATE(waktu) = %s
            GROUP BY HOUR(waktu)
            ORDER BY hour
        """, (today,))
        hourly_data = cursor.fetchall()
        
        # Create hourly chart data
        hours = list(range(24))
        hour_counts = [0] * 24
        for data in hourly_data:
            if 0 <= data['hour'] < 24:
                hour_counts[data['hour']] = data['count']
        
        cursor.close()
        conn.close()
        
        return render_html('statistics.html',
                         stats=stats,
                         today_stats=today_stats,
                         unique_today=unique_today,
                         top_persons=top_persons,
                         hours=hours,
                         hour_counts=hour_counts)
    
    except mysql.connector.Error as e:
        print(f"[DATABASE ERROR] {e}")
        return render_html('error.html', message="Terjadi kesalahan database"), 500

# ========== API ROUTES FOR AJAX ==========

@app.route('/api/dashboard_data')
def api_dashboard_data():
    """API untuk data dashboard"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get statistics
        cursor.execute("SELECT * FROM statistics ORDER BY last_updated DESC LIMIT 1")
        stats = cursor.fetchone()
        
        # Get today's activity
        today = datetime.now().date()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_today,
                SUM(CASE WHEN status_masuk_keluar = 'masuk' THEN 1 ELSE 0 END) as masuk_today,
                SUM(CASE WHEN status_masuk_keluar = 'keluar' THEN 1 ELSE 0 END) as keluar_today
            FROM logs 
            WHERE DATE(waktu) = %s
        """, (today,))
        today_stats = cursor.fetchone()
        
        # Get recent activity
        cursor.execute("SELECT * FROM logs ORDER BY waktu DESC LIMIT 5")
        recent_activity = cursor.fetchall()
        
        # Convert datetime objects to strings
        for activity in recent_activity:
            if isinstance(activity['waktu'], datetime):
                activity['waktu'] = activity['waktu'].strftime('%H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'statistics': stats,
            'today_stats': today_stats,
            'recent_activity': recent_activity
        })
    
    except mysql.connector.Error as e:
        print(f"[DATABASE ERROR] {e}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/recent_activity')
def api_recent_activity():
    """API untuk aktivitas terkini"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM logs 
            ORDER BY waktu DESC 
            LIMIT 10
        """)
        recent_activity = cursor.fetchall()
        
        # Convert datetime objects to strings
        for activity in recent_activity:
            if isinstance(activity['waktu'], datetime):
                activity['waktu'] = activity['waktu'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify(recent_activity)
    
    except mysql.connector.Error as e:
        print(f"[DATABASE ERROR] {e}")
        return jsonify({"error": "Database error"}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_html('error.html', message="Halaman tidak ditemukan"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_html('error.html', message="Terjadi kesalahan internal server"), 500

if __name__ == '__main__':
    print("[FLASK] Starting Face Recognition Website...")
    print("[FLASK] Website available at: http://localhost:5000")
    
    # Check if required files exist
    required_files = ['index.html', 'logs.html', 'statistics.html', 'error.html']
    for file in required_files:
        if not os.path.exists(file):
            print(f"[WARNING] File {file} tidak ditemukan!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
