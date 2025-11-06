# Konfigurasi global untuk seluruh project - MYSQL SERVER VERSION

# Database Configuration untuk MySQL Server
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'saputra19',
    'database': 'wajah_yolov8_2',
    'port': 3306
}

# Model Paths
MODEL_PATHS = {
    'custom': 'runs/detect/train2/weights/best.pt',
    'default': 'yolov8n.pt',
    'fallback': 'yolov8s.pt'
}

# Face Recognition Settings
FACE_SETTINGS = {
    'threshold': 0.5,
    'consistent_threshold': 0.6,
    'margin_ratio': 0.05,
    'track_timeout': 5.0
}

# Konfigurasi kamera Tapo C200
TAPO_CAMERA_IP = "192.168.1.24"
TAPO_USERNAME = "raflisaputra19"
TAPO_PASSWORD = "saputra19"

# Camera Settings untuk Tapo C200
TAPO_CAMERA_SETTINGS = {
    'rtsp_url': f'rtsp://{TAPO_USERNAME}:{TAPO_PASSWORD}@{TAPO_CAMERA_IP}:554/stream1',
    'width': 640,
    'height': 360,
    'fps': 20,
    'skip_frames': 10,
    'buffer_size': 1,
    'timeout': 10,
    'reconnect_delay': 5,
    'type': 'tapo_rtsp'
}

# Camera Settings untuk Webcam
WEBCAM_SETTINGS = {
    'device_index': 0,  # 0 untuk webcam default
    'width': 640,
    'height': 480,
    'fps': 30,
    'skip_frames': 3,   # Lebih rendah karena webcam biasanya lebih responsif
    'buffer_size': 1,
    'timeout': 5,
    'reconnect_delay': 2,
    'type': 'webcam'
}

# Pilihan kamera aktif (ubah sesuai kebutuhan)
ACTIVE_CAMERA = 'webcam'  # 'webcam' atau 'tapo'

# Pengaturan kamera yang aktif
if ACTIVE_CAMERA == 'webcam':
    CAMERA_SETTINGS = WEBCAM_SETTINGS
else:
    CAMERA_SETTINGS = TAPO_CAMERA_SETTINGS

# Application Settings
APP_SETTINGS = {
    'log_folder': 'face_recognition_logs',
    'log_interval': 20,
    'stats_update_interval': 10,
    'camera_name': 'Webcam' if ACTIVE_CAMERA == 'webcam' else 'Tapo_C200_Office'
}

# Konfigurasi tambahan untuk performa optimal
PERFORMANCE_SETTINGS = {
    'max_workers': 4,
    'queue_size': 32,
    'preprocessing_enabled': True,
    'hardware_acceleration': 'auto'  # auto, cuda, opencl, cpu
}

# Konfigurasi khusus untuk jenis kamera berbeda
CAMERA_PROFILES = {
    'webcam': {
        'low_latency': True,
        'high_speed': True,
        'stable_connection': True,
        'recommended_resolution': (640, 480)
    },
    'tapo_rtsp': {
        'low_latency': False,
        'high_speed': False,
        'stable_connection': False,
        'recommended_resolution': (640, 360),
        'network_optimized': True
    }
}