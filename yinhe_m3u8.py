import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置参数
TARGET_IP_START = "120.232.0.0"   # 起始 IP 地址
TARGET_IP_END = "120.232.255.255"   # 结束 IP 地址
THREAD_COUNT = 200  # 增加并发线程数，提高扫描速度
TIMEOUT = 2  # 超时时间（秒）

# M3U8 文件 URL 模板（IP地址会被动态替换）
M3U8_URL_TEMPLATE = "http://{}/snctcc-tvod.tx-cdn.gitv.tv/gitv_live/G_CCTV-1-HD-265-8M/G_CCTV-1-HD-265-8M.m3u8"
# 存储有效 M3U8 URL 的文件
OUTPUT_FILE = "yinhe_m3u8_urls.txt"

def ip_to_int(ip):
    """将IP地址转换为整数"""
    parts = ip.split('.')
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])

def int_to_ip(num):
    """将整数转换为IP地址"""
    return f"{(num >> 24) & 0xFF}.{(num >> 16) & 0xFF}.{(num >> 8) & 0xFF}.{num & 0xFF}"

def generate_ip_range(start_ip, end_ip):
    """生成IP地址范围（生成器，不占用大量内存）"""
    start = ip_to_int(start_ip)
    end = ip_to_int(end_ip)
    for num in range(start, end + 1):
        yield int_to_ip(num)

def check_m3u8(ip):
    """
    检查指定IP的M3U8文件是否存在。
    如果有效，将结果写入输出文件并打印到控制台。
    """
    m3u8_url = M3U8_URL_TEMPLATE.format(ip)
    try:
        # 添加请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(m3u8_url, timeout=TIMEOUT, headers=headers)
        if response.status_code == 200:
            # 验证返回内容是否包含m3u8标识
            content = response.text
            if '#EXTM3U' in content:
                result_str = m3u8_url
                print(f"✅ 找到可用的 M3U8 URL: {result_str}")
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(result_str + "\n")
                return True
    except requests.RequestException:
        pass
    return False

def main():
    print("=" * 60)
    print("开始扫描 M3U8 地址...")
    print(f"URL模板: {M3U8_URL_TEMPLATE}")
    
    # 计算总IP数
    total_ips = ip_to_int(TARGET_IP_END) - ip_to_int(TARGET_IP_START) + 1
    print(f"扫描范围: {TARGET_IP_START} - {TARGET_IP_END}")
    print(f"总计扫描: {total_ips} 个IP地址")
    print(f"并发线程: {THREAD_COUNT}")
    print(f"超时时间: {TIMEOUT}秒")
    print("=" * 60)
    
    # 运行前清空文件
    open(OUTPUT_FILE, "w").close()
    
    found_count = 0
    processed = 0
    
    # 生成IP列表（使用生成器，不一次性加载所有IP到内存）
    ip_generator = generate_ip_range(TARGET_IP_START, TARGET_IP_END)
    
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        # 提交所有任务
        futures = {executor.submit(check_m3u8, ip): ip for ip in ip_generator}
        
        total_tasks = len(futures)
        print(f"任务已提交: {total_tasks} 个")
        print("开始扫描...\n")
        
        for future in as_completed(futures):
            processed += 1
            if future.result():
                found_count += 1
            
            # 每处理1000个任务输出进度
            if processed % 1000 == 0:
                print(f"📊 进度: {processed}/{total_tasks} ({processed*100//total_tasks}%), 找到: {found_count} 个有效URL")
    
    print("\n" + "=" * 60)
    print(f"✅ 扫描完成！")
    print(f"📊 共扫描: {processed} 个IP地址")
    print(f"🎯 找到: {found_count} 个有效的 M3U8 URL")
    print(f"📁 结果已保存到: {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()
