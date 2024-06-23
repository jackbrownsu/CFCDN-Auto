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

# 结果存储字典（用于去重）
result_ips = {}

# 获取网页内容并筛选数据
for url in urls:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')
            
            # 查找表头
            headers = [th.get_text(strip=True) for th in soup.find_all('th')]
            line_index = -1
            ip_index = -1
            latency_index = -1

            # 找到列的索引
            for i, header in enumerate(headers):
                if header in ['线路名称', '线路', 'Line']:
                    line_index = i
                elif header in ['优选地址', 'IP', 'Address', 'IP地址']:
                    ip_index = i
                elif header in ['平均延迟', '往返延迟', 'latency', '延迟']:
                    latency_index = i

            if line_index == -1 or ip_index == -1 or latency_index == -1:
                continue

            # 遍历表格行
            for row in soup.find_all('tr', class_=re.compile(r'line-cm|line-ct|line-cu')):
                columns = row.find_all('td')
                if len(columns) <= max(line_index, ip_index, latency_index):
                    continue

                # 提取线路名称、IP地址和延迟数据
                line = columns[line_index].get_text(strip=True)
                ip_address = columns[ip_index].get_text(strip=True)
                latency_text = columns[latency_index].get_text(strip=True)

                match = re.match(r'(\d+(\.\d+)?)\s*(ms|毫秒)?', latency_text)
                if match:
                    latency = float(match.group(1))
                    if match.group(3) in ['毫秒', None]:
                        latency = latency  # 保持毫秒不变

                    # 仅保留延迟数据低于目标值的数据
                    if latency < DELAY_THRESHOLD_MS and any(x in line for x in ['移动', '联通', '电信']):
                        result_ips[ip_address] = f"{ip_address}#{line}-{latency:.2f}ms"

            # 再次遍历所有行以处理没有特定class的行
            for row in soup.find_all('tr'):
                columns = row.find_all('td')
                if len(columns) <= max(line_index, ip_index, latency_index):
                    continue

                # 提取线路名称、IP地址和延迟数据
                line = columns[line_index].get_text(strip=True)
                ip_address = columns[ip_index].get_text(strip=True)
                latency_text = columns[latency_index].get_text(strip=True)

                match = re.match(r'(\d+(\.\d+)?)\s*(ms|毫秒)?', latency_text)
                if match:
                    latency = float(match.group(1))
                    if match.group(3) in ['毫秒', None]:
                        latency = latency  # 保持毫秒不变

                    # 仅保留延迟数据低于目标值的数据
                    if latency < DELAY_THRESHOLD_MS and any(x in line for x in ['移动', '联通', '电信']):
                        result_ips[ip_address] = f"{ip_address}#{line}-{latency:.2f}ms"
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")

# 将结果写入到txt文件中
with open("ips_latency.txt", "w") as file:
    for ip_line in result_ips.values():
        file.write(ip_line + "\n")

print("数据已写入 ips_latency.txt 文件")
