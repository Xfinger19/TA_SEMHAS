# face_detector.py
import os
import cv2
import numpy as np
from ultralytics import YOLO
import insightface
from sklearn.metrics.pairwise import cosine_similarity
from deep_sort_realtime.deepsort_tracker import DeepSort
import pandas as pd
from datetime import datetime
import time

from config import FACE_SETTINGS, CAMERA_SETTINGS, MODEL_PATHS

class FaceDetector:
    def __init__(self):
        # Inisialisasi model InsightFace
        print("[INFO] Memuat model InsightFace...")
        self.face_model = insightface.app.FaceAnalysis(name='buffalo_l')
        self.face_model.prepare(ctx_id=0, det_size=(320, 320))
        
        # Inisialisasi Deep SORT tracker
        self.tracker = DeepSort(
            max_age=30,
            n_init=3,
            nms_max_overlap=0.7,
            max_cosine_distance=0.4,
            nn_budget=50
        )
        
        # Variables untuk tracking
        self.tracked_faces = {}
        self.face_counter = {}
        self.next_face_id = 0
        self.track_id_mapping = {}
        self.reverse_track_id_mapping = {}
        self.face_status = {}
        self.face_last_seen = {}
        
        # Logging
        self.log_columns = ["id_log", "consistent_id", "nim_nama", "waktu", "lokasi", "status_masuk_keluar"]
        self.log_df = pd.DataFrame(columns=self.log_columns)
        self.log_counter = 1
        
        # Counting
        self.total_masuk = 0
        self.total_keluar = 0
        self.wajah_di_dalam = 0
        self.unique_faces_detected = set()
        
        # Cache
        self.previous_detections = {}
    
    def load_known_faces(self, folder_path):
        """Memuat wajah yang dikenal dari folder"""
        known_faces = []
        known_names = []
        
        print("[INFO] Memulai loading dataset wajah...")
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(root, file)
                    img = cv2.imread(image_path)
                    if img is not None:
                        # Resize image untuk mempercepat processing
                        img = cv2.resize(img, (320, 320))
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        faces = self.face_model.get(img_rgb)
                        if faces:
                            embedding = faces[0].embedding
                            label = os.path.basename(root)
                            known_faces.append(embedding)
                            known_names.append(label)
                            print(f"[✓] Memuat data wajah '{label}' dari {file}")
                        else:
                            print(f"[!] Tidak ditemukan wajah pada {file}")
                    else:
                        print(f"[✗] Gagal memuat {file}")
        
        print(f"[INFO] Selesai memuat {len(known_faces)} wajah")
        return known_faces, known_names
    
    def recognize_identity_cosine(self, embedding, known_faces, known_names, threshold=0.5):
        """Mengenali identitas dengan cosine similarity"""
        if not known_faces:
            return "Tidak Dikenali", 0
        
        similarities = cosine_similarity([embedding], known_faces)[0]
        best_idx = np.argmax(similarities)
        
        if similarities[best_idx] >= threshold:
            return known_names[best_idx], similarities[best_idx]
        else:
            return "Tidak Dikenali", similarities[best_idx]
    
    def expand_bbox(self, x1, y1, x2, y2, img_shape, margin_ratio=0.05):
        """Menambahkan padding ke bounding box"""
        h, w = img_shape[:2]
        
        box_w = x2 - x1
        box_h = y2 - y1
        
        margin_x = int(box_w * margin_ratio)
        margin_y = int(box_h * margin_ratio)
        
        x1 = max(0, x1 - margin_x)
        y1 = max(0, y1 - margin_y)
        x2 = min(w, x2 + margin_x)
        y2 = min(h, y2 + margin_y)
        
        return int(x1), int(y1), int(x2), int(y2)
    
    def get_color_from_name(self, name):
        """Menghasilkan warna berbeda tiap nama"""
        np.random.seed(abs(hash(name)) % (2**32))
        color = np.random.randint(0, 255, 3).tolist()
        return tuple(map(int, color))
    
    def get_consistent_face_id(self, embedding, threshold=0.6):
        """Mendapatkan ID konsisten berdasarkan embedding wajah"""
        if not self.tracked_faces:
            new_id = self.next_face_id
            self.tracked_faces[new_id] = embedding
            self.next_face_id += 1
            return new_id
        
        similarities = {}
        for face_id, saved_embedding in self.tracked_faces.items():
            similarity = cosine_similarity([embedding], [saved_embedding])[0][0]
            similarities[face_id] = similarity
        
        best_id = max(similarities, key=similarities.get)
        best_similarity = similarities[best_id]
        
        if best_similarity >= threshold:
            alpha = 0.8
            self.tracked_faces[best_id] = alpha * self.tracked_faces[best_id] + (1 - alpha) * embedding
            return best_id
        else:
            new_id = self.next_face_id
            self.tracked_faces[new_id] = embedding
            self.next_face_id += 1
            return new_id
    
    def draw_simple_bbox(self, frame, x1, y1, x2, y2, label, color, confidence=0.0):
        """Menggambar bounding box sederhana"""
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        label_text = f"{label}"
        if confidence > 0:
            label_text += f" ({confidence:.2f})"
        
        (text_width, text_height), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        
        cv2.rectangle(frame, (x1, y1 - text_height - 5), (x1 + text_width + 5, y1), color, -1)
        cv2.putText(frame, label_text, (x1 + 2, y1 - 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def draw_simple_info_panel(self, frame, info_dict):
        """Menggambar panel informasi sederhana"""
        h, w = frame.shape[:2]
        x_start, y_start = 10, 10
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (x_start, y_start), (x_start + 250, y_start + 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        cv2.rectangle(frame, (x_start, y_start), (x_start + 250, y_start + 120), (255, 255, 255), 1)
        
        cv2.putText(frame, "FACE RECOG SYSTEM", (x_start + 10, y_start + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        y_offset = 40
        for key, value in info_dict.items():
            text = f"{key}: {value}"
            cv2.putText(frame, text, (x_start + 10, y_start + y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            y_offset += 20
    
    def get_available_camera(self):
        """Mencari kamera yang tersedia"""
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"[SUCCESS] Kamera ditemukan di index {i}")
                    return cap
                cap.release()
        return None