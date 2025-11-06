import cv2
import time

def test_rtsp_urls():
    """Test semua kemungkinan RTSP URL untuk cari yang paling cepat"""
    
    TAPO_IP = "192.168.1.2"
    USERNAME = "raflisaputra19"
    PASSWORD = "saputra19"
    
    # Semua kemungkinan RTSP URLs untuk Tapo C200
    rtsp_urls = {
        "stream1_1080p": f"rtsp://{USERNAME}:{PASSWORD}@{TAPO_IP}:554/stream1",
        "stream2_360p": f"rtsp://{USERNAME}:{PASSWORD}@{TAPO_IP}:554/stream2", 
        "stream2_tcp": f"rtsp://{USERNAME}:{PASSWORD}@{TAPO_IP}:554/stream2?tcp",
        "main_stream": f"rtsp://{USERNAME}:{PASSWORD}@{TAPO_IP}:554/",
        "low_res": f"rtsp://{USERNAME}:{PASSWORD}@{TAPO_IP}:554/cam/realmonitor?channel=1&subtype=1"
    }
    
    for name, url in rtsp_urls.items():
        print(f"\n🔍 Testing: {name}")
        print(f"URL: {url}")
        
        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        start_time = time.time()
        frames_received = 0
        successful_frames = 0
        
        # Test selama 5 detik
        while time.time() - start_time < 5:
            ret, frame = cap.read()
            frames_received += 1
            
            if ret and frame is not None:
                successful_frames += 1
            
            # Break jika tidak ada frame setelah 2 detik
            if time.time() - start_time > 2 and successful_frames == 0:
                break
        
        cap.release()
        
        success_rate = (successful_frames / frames_received * 100) if frames_received > 0 else 0
        fps = successful_frames / 5.0 if successful_frames > 0 else 0
        
        print(f"✅ Success: {success_rate:.1f}% | FPS: {fps:.1f} | Frames: {successful_frames}")
        
        if fps > 10:
            print(f"🎯 RECOMMENDED: {name}")

if __name__ == "__main__":
    test_rtsp_urls()