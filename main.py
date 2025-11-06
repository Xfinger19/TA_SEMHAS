import cv2
import time
from datetime import datetime
import os
import sys

from config import *
from face_detector import FaceDetector
from database_handler import DatabaseHandler

def clear_screen():
    """Membersihkan layar terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_menu():
    """Menampilkan menu pilihan kamera"""
    clear_screen()
    print("=" * 50)
    print("    🎥 SISTEM FACE RECOGNITION")
    print("=" * 50)
    print("\nPILIH SUMBER KAMERA:")
    print("1. 📷 Webcam (Default)")
    print("2. 🌐 Kamera Tapo C200 (RTSP)")
    print("3. 🔄 Test Koneksi Kamera")
    print("4. ⚙️  Settings Kamera")
    print("5. 🚪 Keluar")
    print("\n" + "=" * 50)
    
    choice = input("Pilih opsi [1-5]: ").strip()
    return choice

def test_camera_connection(camera_type, source):
    """Test koneksi kamera"""
    print(f"\n🔍 Testing {camera_type}...")
    
    cap = cv2.VideoCapture(source)
    
    # Set properti dasar
    if camera_type == "webcam":
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    else:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Tunggu inisialisasi
    time.sleep(2)
    
    success_count = 0
    start_time = time.time()
    
    print("   Menguji koneksi selama 5 detik...")
    
    while time.time() - start_time < 5:
        ret, frame = cap.read()
        if ret and frame is not None:
            success_count += 1
        time.sleep(0.1)
    
    cap.release()
    
    fps = success_count / 5.0
    status = "✅ BERHASIL" if fps > 5 else "❌ GAGAL"
    
    print(f"   Status: {status}")
    print(f"   FPS: {fps:.1f}")
    print(f"   Frames berhasil: {success_count}")
    
    input("\nTekan Enter untuk melanjutkan...")
    return fps > 5

def show_camera_settings():
    """Menampilkan dan mengubah settings kamera"""
    clear_screen()
    print("=" * 50)
    print("    ⚙️  SETTINGS KAMERA")
    print("=" * 50)
    
    print(f"\nWebcam Settings:")
    print(f"   Device Index: {WEBCAM_SETTINGS['device_index']}")
    print(f"   Resolution: {WEBCAM_SETTINGS['width']}x{WEBCAM_SETTINGS['height']}")
    print(f"   FPS: {WEBCAM_SETTINGS['fps']}")
    print(f"   Skip Frames: {WEBCAM_SETTINGS['skip_frames']}")
    
    print(f"\nTapo C200 Settings:")
    print(f"   IP Address: {TAPO_CAMERA_IP}")
    print(f"   Username: {TAPO_USERNAME}")
    print(f"   Resolution: {TAPO_CAMERA_SETTINGS['width']}x{TAPO_CAMERA_SETTINGS['height']}")
    print(f"   FPS: {TAPO_CAMERA_SETTINGS['fps']}")
    print(f"   Skip Frames: {TAPO_CAMERA_SETTINGS['skip_frames']}")
    
    print(f"\n1. Ubah Webcam Settings")
    print(f"2. Ubah Tapo Settings") 
    print(f"3. Kembali ke Menu Utama")
    
    choice = input("\nPilih opsi [1-3]: ").strip()
    return choice

def init_camera(camera_choice):
    """Inisialisasi kamera berdasarkan pilihan"""
    if camera_choice == "webcam":
        print(f"\n📷 Menggunakan WEBCAM (device {WEBCAM_SETTINGS['device_index']})")
        source = WEBCAM_SETTINGS['device_index']
        settings = WEBCAM_SETTINGS
    else:
        print(f"\n🌐 Menggunakan TAPO C200 ({TAPO_CAMERA_IP})")
        source = TAPO_CAMERA_SETTINGS['rtsp_url']
        settings = TAPO_CAMERA_SETTINGS
    
    try:
        cap = cv2.VideoCapture(source)
        
        # Set properti kamera
        if camera_choice == "webcam":
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings['width'])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings['height'])
            cap.set(cv2.CAP_PROP_FPS, settings['fps'])
        else:
            # Untuk RTSP, set buffer size kecil untuk reduce delay
            cap.set(cv2.CAP_PROP_BUFFERSIZE, settings['buffer_size'])
            # Juga set resolusi dan FPS
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings['width'])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings['height'])
            cap.set(cv2.CAP_PROP_FPS, settings['fps'])
        
        # Tunggu inisialisasi
        time.sleep(2)
        
        # Test baca frame
        ret, frame = cap.read()
        if ret and frame is not None:
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"   ✅ Berhasil! {actual_width}x{actual_height} @ {actual_fps:.1f} FPS")
            return cap, settings
        else:
            print(f"   ❌ Gagal membaca frame")
            cap.release()
            return None, None
            
    except Exception as e:
        print(f"   ❌ Error inisialisasi kamera: {e}")
        return None, None

def check_mysql_server():
    """Cek apakah MySQL server berjalan"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            connection_timeout=3
        )
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ MySQL server tidak dapat diakses: {e}")
        return False

def main_face_recognition(camera_choice):
    """Fungsi utama face recognition"""
    print(f"\n🚀 MEMULAI FACE RECOGNITION - {camera_choice.upper()}")
    start_total_time = time.time()
    
    # 1. Load dataset wajah
    print("\n1. 📁 Memuat dataset wajah...")
    face_detector = FaceDetector()
    folder_path = "dataset/original"
    
    known_faces, known_names = face_detector.load_known_faces(folder_path)
    print(f"   ✅ {len(known_faces)} wajah berhasil dimuat")
    
    # 2. Inisialisasi database
    print("\n2. 🗄️ Inisialisasi database...")
    db_initialized = False
    db_handler = None
    
    if check_mysql_server():
        print("   ✅ MySQL server berjalan")
        db_handler = DatabaseHandler()
        db_initialized = db_handler.init_database()
        
        if not db_initialized:
            print("   ⚠️  Database tidak terhubung")
    else:
        print("   ❌ MySQL server tidak berjalan")
    
    # 3. Load model YOLO
    print("\n3. 🤖 Memuat model YOLO...")
    model_options = [
        MODEL_PATHS['default'],
        MODEL_PATHS['custom'],
        MODEL_PATHS['fallback']
    ]
    
    model = None
    for model_path in model_options:
        print(f"   Mencoba: {model_path}")
        try:
            if not os.path.exists(model_path):
                print(f"   ❌ File tidak ditemukan: {model_path}")
                continue
                
            from ultralytics import YOLO
            model = YOLO(model_path)
            print(f"   ✅ Model {model_path} berhasil dimuat!")
            break
        except Exception as e:
            print(f"   ❌ Gagal memuat model {model_path}: {e}")
            continue
    
    if model is None:
        print("   ❌ Semua model gagal dimuat!")
        return
    
    # 4. Buka kamera
    cap, camera_settings = init_camera(camera_choice)
    if cap is None:
        print("   ❌ Gagal membuka kamera!")
        return
    
    total_start_time = time.time() - start_total_time
    print(f"\n🎯 SISTEM SIAP! Waktu startup: {total_start_time:.2f} detik")
    print(f"   📊 Status Database: {'✅ TERHUBUNG' if db_initialized else '❌ TIDAK TERHUBUNG'}")
    print("   Kontrol: 'q'=keluar, 'r'=reset, 's'=save log, 'p'=pause")
    
    # Variabel untuk main loop
    frame_count = 0
    frame_skip_counter = 0
    fps_update_time = time.time()
    last_fps_count = 0
    pause = False
    
    try:
        while True:
            if not pause:
                ret, frame = cap.read()
                if not ret:
                    print("[ERROR] Gagal membaca frame!")
                    time.sleep(0.1)
                    continue
                
                frame_count += 1
                frame_skip_counter += 1
                
                # Skip frame untuk performa
                if frame_skip_counter % camera_settings['skip_frames'] != 0:
                    continue
                
                # Resize frame untuk performa
                if frame.shape[1] > 640:
                    frame = cv2.resize(frame, (640, 480))
                
                # Deteksi dengan YOLO
                try:
                    results = model(frame, verbose=False)[0]
                    detections = []
                    
                    for box in results.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = box.conf[0].item()
                        cls_id = int(box.cls[0])
                        class_name = results.names[cls_id]
                        
                        if conf < 0.5:
                            continue
                        
                        # Expand bounding box
                        x1, y1, x2, y2 = face_detector.expand_bbox(x1, y1, x2, y2, frame.shape)
                        
                        bbox = [x1, y1, x2-x1, y2-y1]
                        detections.append((bbox, conf, class_name))
                    
                    # Update tracker
                    tracks = face_detector.tracker.update_tracks(detections, frame=frame)
                    current_frame_faces = set()
                    faces_detected_count = 0
                    
                    # Process tracks
                    for track in tracks:
                        if not track.is_confirmed():
                            continue
                        
                        track_id = track.track_id
                        ltrb = track.to_ltrb()
                        x1, y1, x2, y2 = map(int, ltrb)
                        
                        # Pastikan bounding box dalam frame
                        x1 = max(0, x1)
                        y1 = max(0, y1)
                        x2 = min(frame.shape[1], x2)
                        y2 = min(frame.shape[0], y2)
                        
                        # Ambil crop wajah
                        face_crop = frame[y1:y2, x1:x2]
                        if face_crop.size == 0:
                            continue
                        
                        # Deteksi wajah dengan InsightFace
                        try:
                            rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                            faces = face_detector.face_model.get(rgb_crop)
                            
                            if faces:
                                embedding = faces[0].embedding
                                name, similarity = face_detector.recognize_identity_cosine(
                                    embedding, known_faces, known_names, FACE_SETTINGS['threshold']
                                )
                                
                                consistent_id = face_detector.get_consistent_face_id(embedding)
                                current_frame_faces.add(consistent_id)
                                
                                # Periksa status masuk/keluar
                                current_time = time.time()
                                if consistent_id not in face_detector.face_status:
                                    face_detector.face_status[consistent_id] = "masuk"
                                    face_detector.face_last_seen[consistent_id] = current_time
                                    
                                    # Add log entry
                                    face_detector.total_masuk += 1
                                    face_detector.wajah_di_dalam += 1
                                    face_detector.unique_faces_detected.add(consistent_id)
                                    
                                    # Simpan ke database jika terhubung
                                    if db_initialized:
                                        success = db_handler.save_log(consistent_id, name, "masuk")
                                        if success:
                                            print(f"[LOG] ID:{consistent_id} | {name} | MASUK")
                                        else:
                                            print(f"[LOG] ID:{consistent_id} | {name} | MASUK (DB FAILED)")
                                    else:
                                        print(f"[LOG] ID:{consistent_id} | {name} | MASUK")
                                    
                                else:
                                    face_detector.face_last_seen[consistent_id] = current_time
                                
                                if consistent_id not in face_detector.face_counter:
                                    face_detector.face_counter[consistent_id] = name
                                
                                faces_detected_count = len(set(face_detector.face_counter.values())) - (1 if "Tidak Dikenali" in set(face_detector.face_counter.values()) else 0)
                                
                                # Gambar bounding box
                                color = face_detector.get_color_from_name(name)
                                label_text = f"ID:{consistent_id} {name}"
                                face_detector.draw_simple_bbox(frame, x1, y1, x2, y2, label_text, color, similarity)
                        
                        except Exception as face_error:
                            continue
                    
                    # Periksa wajah yang keluar
                    current_time = time.time()
                    for consistent_id in list(face_detector.face_last_seen.keys()):
                        if consistent_id not in current_frame_faces:
                            if (current_time - face_detector.face_last_seen[consistent_id] > FACE_SETTINGS['track_timeout'] and 
                                face_detector.face_status.get(consistent_id) == "masuk"):
                                face_detector.face_status[consistent_id] = "keluar"
                                name = face_detector.face_counter.get(consistent_id, "Tidak Dikenali")
                                
                                face_detector.total_keluar += 1
                                face_detector.wajah_di_dalam = max(0, face_detector.wajah_di_dalam - 1)
                                
                                # Simpan ke database jika terhubung
                                if db_initialized:
                                    success = db_handler.save_log(consistent_id, name, "keluar")
                                    if success:
                                        print(f"[LOG] ID:{consistent_id} | {name} | KELUAR")
                                    else:
                                        print(f"[LOG] ID:{consistent_id} | {name} | KELUAR (DB FAILED)")
                                else:
                                    print(f"[LOG] ID:{consistent_id} | {name} | KELUAR")
                                
                except Exception as yolo_error:
                    continue
                
                # Hitung FPS
                current_time = time.time()
                if current_time - fps_update_time >= 1.0:
                    fps = (frame_count - last_fps_count) / (current_time - fps_update_time)
                    fps_update_time = current_time
                    last_fps_count = frame_count
                else:
                    fps = 0
                
                # Info panel
                camera_type = "WEBCAM" if camera_choice == "webcam" else "TAPO C200"
                info_dict = {
                    "Kamera": camera_type,
                    "Wajah": faces_detected_count,
                    "Track": len(tracks),
                    "Masuk": face_detector.total_masuk,
                    "Keluar": face_detector.total_keluar,
                    "Di Dalam": face_detector.wajah_di_dalam,
                    "FPS": f"{fps:.1f}"
                }
                
                face_detector.draw_simple_info_panel(frame, info_dict)
                
                # Tampilkan status pause
                if pause:
                    cv2.putText(frame, "PAUSED", (frame.shape[1]//2 - 50, frame.shape[0]//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Tampilkan frame
            window_title = f"Face Recognition - {camera_type}"
            cv2.imshow(window_title, frame)
            
            # Input handling
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                # Reset counting
                face_detector.total_masuk = 0
                face_detector.total_keluar = 0
                face_detector.wajah_di_dalam = 0
                face_detector.unique_faces_detected = set()
                print("[INFO] Counting telah direset")
            elif key == ord('s'):
                print("[INFO] Menyimpan log manual...")
            elif key == ord('p'):
                pause = not pause
                status = "PAUSED" if pause else "RESUMED"
                print(f"[INFO] {status}")
            
            # Update statistics secara periodic jika database terhubung
            if not pause and db_initialized and db_handler and frame_count % APP_SETTINGS['stats_update_interval'] == 0:
                db_handler.update_statistics(
                    face_detector.total_masuk, 
                    face_detector.total_keluar, 
                    face_detector.wajah_di_dalam, 
                    len(face_detector.unique_faces_detected)
                )
    
    except Exception as main_error:
        print(f"[CRITICAL ERROR] {main_error}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\n[INFO] Melakukan cleanup...")
        cap.release()
        cv2.destroyAllWindows()
        
        # Final statistics update jika database terhubung
        if db_initialized and db_handler:
            db_handler.update_statistics(
                face_detector.total_masuk, 
                face_detector.total_keluar, 
                face_detector.wajah_di_dalam, 
                len(face_detector.unique_faces_detected)
            )
        
        print("\n=== SUMMARY ===")
        print(f"Kamera: {camera_type}")
        print(f"Total Masuk: {face_detector.total_masuk}")
        print(f"Total Keluar: {face_detector.total_keluar}")
        print(f"Wajah di Dalam: {face_detector.wajah_di_dalam}")
        print(f"Unique Faces: {len(face_detector.unique_faces_detected)}")
        print(f"Total Frame: {frame_count}")

def main():
    """Program utama dengan menu interaktif"""
    while True:
        choice = show_menu()
        
        if choice == '1':
            # Webcam
            main_face_recognition("webcam")
            
        elif choice == '2':
            # Tapo C200
            main_face_recognition("tapo")
            
        elif choice == '3':
            # Test koneksi kamera
            clear_screen()
            print("🔍 TEST KONEKSI KAMERA")
            print("=" * 30)
            
            print("\n1. Test Webcam")
            print("2. Test Tapo C200")
            print("3. Kembali")
            
            test_choice = input("\nPilih [1-3]: ").strip()
            
            if test_choice == '1':
                test_camera_connection("Webcam", WEBCAM_SETTINGS['device_index'])
            elif test_choice == '2':
                test_camera_connection("Tapo C200", TAPO_CAMERA_SETTINGS['rtsp_url'])
            elif test_choice == '3':
                continue
            else:
                print("Pilihan tidak valid!")
                
        elif choice == '4':
            # Settings kamera
            settings_choice = show_camera_settings()
            if settings_choice == '3':
                continue
            else:
                print("\n⚠️  Fitur ubah settings sedang dalam pengembangan...")
                input("Tekan Enter untuk melanjutkan...")
                
        elif choice == '5':
            # Keluar
            print("\n👋 Terima kasih telah menggunakan sistem Face Recognition!")
            sys.exit(0)
            
        else:
            print("\n❌ Pilihan tidak valid! Silakan pilih 1-5.")
            input("Tekan Enter untuk melanjutkan...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program dihentikan oleh user")
        sys.exit(0)