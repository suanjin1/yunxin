import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置参数
TARGET_IP_START = "120.232.0.0"   # 起始 IP 地址
TARGET_IP_END = "120.232.255.255"   # 结束 IP 地址
THREAD_COUNT = 100                 # 并发线程数

# M3U8 文件 URL 模板（IP地址会被动态替换）
M3U8_URL_TEMPLATE = "http://{}/snctcc-tvod.tx-cdn.gitv.tv/gitv_live/G_CCTV-1-HD-265-8M/G_CCTV-1-HD-265-8M.m3u8"
# 存储有效 M3U8 URL 的文件
OUTPUT_FILE = "yinhe_m3u8_urls.txt"

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

def check_m3u8(ip, output_file):
    """
    检查指定IP的M3U8文件是否存在。
    如果有效，将结果写入输出文件并打印到控制台。
    """
    m3u8_url = M3U8_URL_TEMPLATE.format(ip)
    try:
        response = requests.get(m3u8_url, timeout=3)
        if response.status_code == 200:
            result_str = m3u8_url
            print(f"找到可用的 M3U8 URL: {result_str}")
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(result_str + "\n")
    except requests.RequestException:
        pass

def main():
    ip_list = list(generate_ip_range(TARGET_IP_START, TARGET_IP_END))
    total_ips = len(ip_list)
    print(f"开始扫描 {total_ips} 个IP地址，使用 {THREAD_COUNT} 线程...")
    print(f"URL模板: {M3U8_URL_TEMPLATE}")

    # 运行前清空文件，保证只记录最新结果
    open(OUTPUT_FILE, "w").close()

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = {executor.submit(check_m3u8, ip, OUTPUT_FILE): ip for ip in ip_list}
        
        total_tasks = len(futures)
        completed = 0

        for future in as_completed(futures):
            future.result()
            completed += 1
            if completed % 1000 == 0:
                print(f"已完成 {completed} / {total_tasks} 个任务")

    print(f"\n扫描完成，所有有效的M3U8 URL已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
