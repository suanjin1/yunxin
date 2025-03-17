import requests
from Crypto.Cipher import AES
import base64
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置参数
TARGET_URL_TEMPLATE = "https://apiappdyyztvyydsqwdy.68.gy:{}/api.php/getappapi.index/vodDetail"
START_PORT = 5689  # 起始端口
END_PORT = 5690  # 结束端口
THREAD_COUNT = 100  # 并发线程数（可以根据网络情况调整）

# AES 解密函数
def decrypt(data, key="dyyztvapiappyyds", iv="dyyztvapiappyyds"):
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    decrypted = cipher.decrypt(base64.b64decode(data))
    return decrypted.rstrip(b'\0').decode('utf-8')

# 获取 API 数据
def get_data_from_url(port):
    url = TARGET_URL_TEMPLATE.format(port)
    post_data = {'vod_id': '519445'}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": f"https://apiappdyyztvyydsqwdy.68.gy:{port}"
    }
    
    try:
        response = requests.get(url, params=post_data, headers=headers, timeout=5)
        if response.status_code == 200:
            response_data = json.loads(response.text)
            if 'data' in response_data:
                decrypted_data = decrypt(response_data['data'])
                return port, decrypted_data  # 返回端口和解密数据
    except requests.RequestException:
        pass
    
    return port, None

# 多线程扫描端口
def check_ports():
    valid_ports = []  # 记录有效端口

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = {executor.submit(get_data_from_url, port): port for port in range(START_PORT, END_PORT + 1)}

        for future in as_completed(futures):
            port, decrypted_data = future.result()
            if decrypted_data:
                print(f"✅ Port {port} has data: {decrypted_data[:100]}...")
                valid_ports.append(f"Port {port} has data: {decrypted_data[:100]}...\n")

    # 保存有效端口到文件
    if valid_ports:
        with open('valid_ports.txt', 'w', encoding='utf-8') as file:
            file.writelines(valid_ports)
        print(f"\n🔍 扫描完成，有效端口已保存到 valid_ports.txt")
    else:
        print("\n❌ 扫描完成，未找到有效端口！")

if __name__ == "__main__":
    check_ports()
