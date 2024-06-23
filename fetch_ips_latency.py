import requests
import re

# 配置多个网址
urls = [
    "https://cf.090227.xyz/",
    "https://stock.hostmonit.com/CloudFlareYes",
    "https://ip.164746.xyz/",
    "https://monitor.gacjie.cn/page/cloudflare/ipv4.html",
    "https://345673.xyz/#"
]

# 目标延迟阈值
DELAY_THRESHOLD_MS = 200

# 结果存储列表
result_ips = set()

# 正则表达式模式匹配
ip_pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
line_pattern = re.compile(r'(线路名称|Line|线路).+?(\w+)')  # 匹配线路名称
latency_pattern = re.compile(r'(平均延迟|往返延迟|Latency).+?(\d+)\s*(ms|毫秒)')  # 匹配延迟数据

# 获取网页内容并筛选数据
for url in urls:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # 匹配 IP 地址
            ip_matches = ip_pattern.findall(content)
            
            # 匹配线路名称
            line_match = line_pattern.search(content)
            if line_match:
                line = line_match.group(2).strip()
            else:
                line = ""
            
            # 匹配延迟数据
            latency_match = latency_pattern.search(content)
            if latency_match:
                latency = f"{latency_match.group(2)}{latency_match.group(3)}"
            else:
                latency = ""
            
            # 组装结果
            for ip in ip_matches:
                if line and latency:
                    result_ips.add(f"{ip}#{line}-{latency}")
                elif line:
                    result_ips.add(f"{ip}#{line}")
                else:
                    result_ips.add(f"{ip}")
                    
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")

# 将结果写入到txt文件中
with open("ips_latency.txt", "w") as file:
    for ip_line in result_ips:
        file.write(ip_line + "\n")

print("数据已写入 ips_latency.txt 文件")
