import os
import time
import hmac
import hashlib
import requests
import json

# ==================== [ CONFIGURATION FROM SECRETS ] ====================
ACCESS_ID = os.environ.get("TUYA_ACCESS_ID")
ACCESS_SECRET = os.environ.get("TUYA_ACCESS_SECRET")
DEVICE_ID = "a3e275b15e7bcd03f6rtj9"

# ดึงผ่านเซิร์ฟเวอร์หลักภูมิภาคเอเชียแปซิฟิก (Singapore Data Center ที่คุณใช้งาน)
TUYA_BASE_URL = "https://tuya-asia.com"
# =========================================================================

def generate_signature(client_id, secret, timestamp, access_token="", body=""):
    """ฟังก์ชันคำนวณรหัสความปลอดภัยตามมาตรฐานล่าสุดของ Tuya API v2.0"""
    http_method = "GET"
    url_path = f"/v1.0/devices/{DEVICE_ID}/status"
    
    # แปลงบอดี้ว่างให้เป็นค่าแฮช sha256 
    content_sha = hashlib.sha256(body.encode('utf-8')).hexdigest()
    
    # จัดเรียง string ข้อมูลตามโครงสร้างที่ Tuya กำหนด
    string_to_sign = f"{http_method}\n{content_sha}\n\n{url_path}"
    message = client_id + access_token + str(timestamp) + string_to_sign
    
    # ถอดรหัสลับความปลอดภัยออกมาเป็นค่า Sign ตัวใหญ่
    return hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest().upper()

def get_access_token():
    """ฟังก์ชันขอรหัสผ่านชั่วคราวในการเข้าถึงข้อมูลอุปกรณ์"""
    if not ACCESS_ID or not ACCESS_SECRET:
        print("❌ ข้อผิดพลาด: ไม่พบค่า TUYA_ACCESS_ID หรือ TUYA_ACCESS_SECRET ในระบบ GitHub Secrets!")
        return None
        
    timestamp = int(time.time() * 1000)
    url_path = "/v1.0/token?grant_type=1"
    content_sha = hashlib.sha256("".encode('utf-8')).hexdigest()
    string_to_sign = f"GET\n{content_sha}\n\n{url_path}"
    message = ACCESS_ID + str(timestamp) + string_to_sign
    sign = hmac.new(ACCESS_SECRET.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    
    headers = {
        "client_id": ACCESS_ID,
        "sign": sign,
        "t": str(timestamp),
        "sign_method": "HMAC-SHA256"
    }
    
    try:
        response = requests.get(f"{TUYA_BASE_URL}{url_path}", headers=headers, timeout=10)
        result = response.json()
        if result.get("success"):
            return result["result"]["access_token"]
        else:
            print("❌ ไม่สามารถขอ Token ได้เนื่องจากระบบ Tuya แจ้งปฏิเสธ:", result)
            return None
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อไปยังเซิร์ฟเวอร์ Tuya: {str(e)}")
        return None

def fetch_weather_and_save():
    """ฟังก์ชันหลักในการดึงค่าเซ็นเซอร์สภาพอากาศและเขียนไฟล์รายงาน"""
    token = get_access_token()
    if not token: 
        return
        
    timestamp = int(time.time() * 1000)
    sign = generate_signature(ACCESS_ID, ACCESS_SECRET, timestamp, access_token=token)
    
    headers = {
        "client_id": ACCESS_ID,
        "access_token": token,
        "sign": sign,
        "t": str(timestamp),
        "sign_method": "HMAC-SHA256"
    }
    
    try:
        device_url = f"{TUYA_BASE_URL}/v1.0/devices/{DEVICE_ID}/status"
        response = requests.get(device_url, headers=headers, timeout=10)
        weather_data = response.json()
        
        if weather_data.get("success"):
            payload = weather_data["result"]
            
            # บันทึกข้อมูลสถานะลงเป็นไฟล์ประเภท JSON ดิบ

            current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "weather.json")

with open(file_path, "w", encoding="utf-8") as f:
    
                json.dump(payload, f, ensure_ascii=False, indent=4)
            print("✅ ประสบความสำเร็จ: ดึงข้อมูลและอัปเดตไฟล์ weather.json เรียบร้อยแล้ว!")
        else:
            print("❌ เกิดข้อผิดพลาดในการดึงสถานะอุปกรณ์:", weather_data)
            
    except Exception as e:
        print(f"❌ ระบบไม่สามารถเขียนไฟล์หรือดึงข้อมูลสภาพอากาศได้: {str(e)}")

if __name__ == "__main__":
    fetch_weather_and_save()
