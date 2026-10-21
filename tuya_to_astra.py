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
TUYA_BASE_URL = "https://tuyaeu.com"

# =========================================================================

def generate_signature(client_id, secret, timestamp, access_token="", body=""):
    http_method = "GET"
    url_path = f"/v1.0/devices/{DEVICE_ID}/status"
    content_sha = hashlib.sha256(body.encode('utf-8')).hexdigest()
    string_to_sign = f"{http_method}\n{content_sha}\n\n{url_path}"
    message = client_id + access_token + str(timestamp) + string_to_sign
    return hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest().upper()

def get_access_token():
    timestamp = int(time.time() * 1000)
    url_path = "/v1.0/token?grant_type=1"
    content_sha = hashlib.sha256("".encode('utf-8')).hexdigest()
    string_to_sign = f"GET\n{content_sha}\n\n{url_path}"
    message = ACCESS_ID + str(timestamp) + string_to_sign
    sign = hmac.new(ACCESS_SECRET.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest().upper()
    
    headers = {"client_id": ACCESS_ID, "sign": sign, "t": str(timestamp), "sign_method": "HMAC-SHA256"}
    response = requests.get(f"{TUYA_BASE_URL}{url_path}", headers=headers, timeout=10)
    result = response.json()
    return result["result"]["access_token"] if result.get("success") else None

def fetch_weather_and_save():
    token = get_access_token()
    if not token: 
        print("❌ ไม่สามารถดึงรหัส Access Token ได้")
        return
        
    timestamp = int(time.time() * 1000)
    sign = generate_signature(ACCESS_ID, ACCESS_SECRET, timestamp, access_token=token)
    
    headers = {"client_id": ACCESS_ID, "access_token": token, "sign": sign, "t": str(timestamp), "sign_method": "HMAC-SHA256"}
    device_url = f"{TUYA_BASE_URL}/v1.0/devices/{DEVICE_ID}/status"
    response = requests.get(device_url, headers=headers, timeout=10)
    weather_data = response.json()
    
    if weather_data.get("success"):
        payload = weather_data["result"]
        # คำสั่งสร้างไฟล์แบบปลอดภัยและแน่นอน
        with open("weather.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
        print("✅ ดึงและเซฟข้อมูล Tuya ลงไฟล์ weather.json สำเร็จ!")
    else:
        print("❌ ดึงข้อมูลผิดพลาด:", weather_data)

if __name__ == "__main__":
    fetch_weather_and_save()
