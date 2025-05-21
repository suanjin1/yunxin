import socket
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置参数
TARGET_IP_START = "110.42.1.1"   # 起始 IP 地址
TARGET_IP_END = "110.42.255.254" # 结束 IP 地址
PORT_START =  35455              # 起始端口
PORT_END = 35455                 # 结束端口
THREAD_COUNT =  100               # 并发线程数，降低线程数防止 GitHub Actions 限制 CPU 资源

# M3U8 文件 URL 模板
M3U8_URL_TEMPLATE = "http://{}:{}/itv/1000000005000265001.m3u8?cdn=ystenlive"

# 存储有效 M3U8 URL 的文件
OUTPUT_FILE = "valid_yigeip_urls.txt"

# 共享变量：用于标记是否找到可用的 M3U8 URL
found_flag = False
lock = threading.Lock()

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

def scan_port(ip, port):
    """
    检查指定IP和端口是否开放，并验证M3U8文件是否存在。
    如果找到第一个可用的M3U8 URL，则停止所有扫描任务。
    """
    global found_flag
    if found_flag:
        return  # 如果已经找到结果，则立即返回，不再执行检查

    try:
        # 创建 TCP 连接，检查端口是否开放
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)  # 降低超时时间，提高扫描速度
            result = sock.connect_ex((ip, port))
            if result == 0:  # 端口开放
                m3u8_url = M3U8_URL_TEMPLATE.format(ip, port)
                try:
                    # 发送 HTTP 请求检查 M3U8 文件是否存在
                    response = requests.get(m3u8_url, timeout=5)  # 设置请求超时，防止长时间卡住
                    if response.status_code == 200:
                        with lock:  # 线程锁，防止多个线程同时写入
                            if not found_flag:  # 额外检查，防止多次写入
                                found_flag = True  # 设置全局变量，停止所有扫描任务
                                result_str = f"[{ip}:{port}]"  # 如果需要完整URL改成 `{m3u8_url}`
                                print(f"找到可用的 M3U8 URL: {result_str} {m3u8_url}")
                                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                                    f.write(result_str + "\n")
                except requests.RequestException:
                    pass  # 请求异常时跳过
    except Exception:
        pass  # 端口扫描异常时跳过

def main():
    """
    执行主扫描任务：
    1. 生成 IP 地址范围
    2. 多线程扫描端口
    3. 在找到第一个可用的 M3U8 URL 后立即停止所有线程
    """
    global found_flag

    # 生成所有需要扫描的 IP 地址
    ip_list = list(generate_ip_range(TARGET_IP_START, TARGET_IP_END))
    total_ips = len(ip_list)

    print(f"开始扫描 {total_ips} 个IP地址，每个IP扫描 {PORT_START} 到 {PORT_END} 端口，使用 {THREAD_COUNT} 线程...")

    # 运行前清空文件，保证只记录最新结果
    open(OUTPUT_FILE, "w").close()

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = []
        
        # 提前检查 found_flag，避免提交不必要的任务
        for ip in ip_list:
            if found_flag:
                break  # 如果已经找到结果，停止提交新任务
            for port in range(PORT_START, PORT_END + 1):
                future = executor.submit(scan_port, ip, port)
                futures.append(future)
                time.sleep(0.01)  # 避免 GitHub Actions 过载，降低请求频率

        # 遍历任务，如果找到可用URL，立即停止所有任务
        for future in as_completed(futures):
            if found_flag:
                break  # 直接跳出循环，避免继续执行无用任务
            try:
                future.result()  # 确保异常被捕获
            except Exception:
                pass  # 忽略异常，防止任务失败

    print(f"\n扫描完成，结果已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
