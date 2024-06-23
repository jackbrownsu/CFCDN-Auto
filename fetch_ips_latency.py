import requests
from bs4 import BeautifulSoup
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

# 获取网页内容并筛选数据
for url in urls:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取所有的 <th> 标签
            th_tags = soup.find_all('th')
            
            # 初始化线路和延迟数据
            line = ""
            latency = ""
            
            # 找到线路名称
            for th in th_tags:
                th_text = th.get_text(strip=True)
                
                # 匹配线路名称
                if th_text in ['线路名称', '线路', 'Line']:
                    line = th_text
                
                # 匹配延迟数据
                elif th_text in ['平均延迟', '往返延迟', 'latency', '延迟']:
                    latency_th = th.find_next_sibling('td')
                    if latency_th:
                        latency_text = latency_th.get_text(strip=True)
                        # 匹配数字和可能的单位，统一为 ms
                        match = re.match(r'(\d+(\.\d+)?)\s*(ms|毫秒)?', latency_text)
                        if match:
                            latency = f"{match.group(1)}ms"
                    
                    # 根据 IP 地址设置结果
                    for ip_match in re.finditer(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', content):
                        result_ips.add(f"{ip_match.group()}#{line}-{latency}")
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")

# 将结果写入到txt文件中
with open("ips_latency.txt", "w") as file:
    for ip_line in result_ips:
        file.write(ip_line + "\n")

print("数据已写入 ips_latency.txt 文件")
