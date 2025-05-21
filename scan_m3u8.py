import socket
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置参数
TARGET_IP_START = "110.42.1.1"   # 起始 IP 地址
TARGET_IP_END = "110.42.254.254"   # 结束 IP 地址
PORT_START = 35455                 # 起始端口
PORT_END = 35455                   # 结束端口
THREAD_COUNT = 100                 # 并发线程数

# M3U8 文件 URL 模板
M3U8_URL_TEMPLATE = "http://{}:{}/bptv/10000100000000050000000003864351.m3u8"
# 存储有效 M3U8 URL 的文件
OUTPUT_FILE = "valid_m3u8_urls.txt"

def ip_to_int(ip):
    """将IP地址转换为整数"""
    return sum(int(num) << (8 * i) for i, num in enumerate(reversed(ip.split('.'))))

def int_to_ip(num):
    """将整数转换为IP地址"""
    return '.'.join(str((num >> (8 * i)) & 0xFF) for i in reversed(range(4)))

def generate_ip_range(start_ip, end_ip):
    """生成IP地址范围"""
    start = ip_to_int(start_ip)
    end = ip_to_int(end_ip)
    for num in range(start, end + 1):
        yield int_to_ip(num)

def scan_port(ip, port, output_file):
    """
    检查指定IP和端口是否开放，并验证M3U8文件是否存在。
    如果有效，将结果写入输出文件并打印到控制台。
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)  # 设置超时时间为0.5秒
            result = sock.connect_ex((ip, port))
            if result == 0:
                m3u8_url = M3U8_URL_TEMPLATE.format(ip, port)
                try:
                    response = requests.get(m3u8_url, timeout=5)
                    if response.status_code == 200:                        
                        result_str = f"{ip}:{port}"  # 如果需要完整URL改成:[{ip}:{port}] {m3u8_url}
                        print(f"找到可用的 M3U8 URL: {result_str} {m3u8_url}")                        
                        with open(output_file, "a", encoding="utf-8") as f:
                            f.write(result_str + "\n")
                except requests.RequestException:
                    pass
    except Exception:
        pass

def main():
    ip_list = list(generate_ip_range(TARGET_IP_START, TARGET_IP_END))
    total_ips = len(ip_list)
    total_ports = PORT_END - PORT_START + 1
    print(f"开始扫描 {total_ips} 个IP地址，每个IP扫描 {PORT_START} 到 {PORT_END} 端口，使用 {THREAD_COUNT} 线程...")

    # 运行前清空文件，保证只记录最新结果
    open(OUTPUT_FILE, "w").close()

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = {executor.submit(scan_port, ip, port, OUTPUT_FILE): (ip, port)
                   for ip in ip_list
                   for port in range(PORT_START, PORT_END + 1)}

        total_tasks = len(futures)

        for future in as_completed(futures):
            future.result()
            if len(futures) % 1000 == 0:
                print(f"已完成 {total_tasks - len(futures)} / {total_tasks} 个任务")

    print(f"\n扫描完成，所有有效的M3U8 URL已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
