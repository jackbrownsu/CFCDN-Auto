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
DELAY_THRESHOLD_MS = 100

# 结果存储列表
result_ips = set()

# 获取网页内容并筛选数据
for url in urls:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找所有表格行
            rows = soup.find_all('tr')
            for row in rows:
                columns = row.find_all('th')
                if len(columns) == 0:
                    continue

                # 初始化线路和延迟数据
                line = ""
                latency = ""
                ip_address = ""

                for th in columns:
                    th_text = th.get_text(strip=True)
                    
                    # 查找线路名称
                    if th_text in ['线路名称', '线路', 'Line']:
                        line_td = th.find_next('td')
                        if line_td:
                            line = line_td.get_text(strip=True)
                    
                    # 查找延迟数据
                    if th_text in ['平均延迟', '往返延迟', 'latency', '延迟']:
                        latency_td = th.find_next('td')
                        if latency_td:
                            latency_text = latency_td.get_text(strip=True)
                            match = re.match(r'(\d+(\.\d+)?)\s*(ms|毫秒)?', latency_text)
                            if match:
                                latency = float(match.group(1))
                                if match.group(3) == '毫秒':
                                    latency = latency / 1  # 将毫秒转为ms

                # 查找IP地址
                for td in row.find_all('td'):
                    ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', td.get_text(strip=True))
                    if ip_match:
                        ip_address = ip_match.group()

                # 如果线路名称和延迟数据均匹配到，且延迟小于目标值，保存结果
                if ip_address and latency and latency < DELAY_THRESHOLD_MS:
                    result_ips.add(f"{ip_address}#{line}-{latency:.2f}ms")
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")

# 将结果写入到txt文件中
with open("ips_latency.txt", "w") as file:
    for ip_line in result_ips:
        file.write(ip_line + "\n")

print("数据已写入 ips_latency.txt 文件")
