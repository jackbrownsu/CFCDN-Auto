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

def fetch_and_parse(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def extract_data_cf_090227(soup):
    for row in soup.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) < 3:
            continue

        ip_address = columns[1].get_text(strip=True)
        latency_text = columns[2].get_text(strip=True)
        line = columns[0].get_text(strip=True)

        match = re.match(r'(\d+(\.\d+)?)\s*(ms|毫秒)?', latency_text)
        if match:
            latency = float(match.group(1))
            if match.group(3) in ['毫秒', None]:
                latency = latency  # 保持毫秒不变

            # 仅保留延迟数据低于目标值的数据
            if latency < DELAY_THRESHOLD_MS:
                result_ips[ip_address] = f"{ip_address}#{line}-{latency:.2f}ms"

def extract_data_general(soup, url):
    headers = [th.get_text(strip=True) for th in soup.find_all('th')]
    line_index, ip_index, latency_index = -1, -1, -1

    # 找到列的索引
    for i, header in enumerate(headers):
        if header in ['线路名称', '线路', 'Line']:
            line_index = i
        elif header in ['优选地址', 'IP', 'Address', 'IP地址']:
            ip_index = i
        elif header in ['平均延迟', '往返延迟', 'latency', '延迟']:
            latency_index = i

    if line_index == -1 or ip_index == -1 or latency_index == -1:
        return

    # 遍历表格行
    for row in soup.find_all('tr', class_=re.compile(r'line-cm|line-ct|line-cu')):
        columns = row.find_all('td')
        if len(columns) <= max(line_index, ip_index, latency_index):
            continue
        process_row(columns, line_index, ip_index, latency_index)

    # 再次遍历所有行以处理没有特定class的行
    for row in soup.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) <= max(line_index, ip_index, latency_index):
            continue
        process_row(columns, line_index, ip_index, latency_index)

def process_row(columns, line_index, ip_index, latency_index):
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

for url in urls:
    soup = fetch_and_parse(url)
    if soup:
        if url == "https://cf.090227.xyz/":
            extract_data_cf_090227(soup)
        else:
            extract_data_general(soup, url)

# 将结果写入到txt文件中
with open("ips_latency.txt", "w") as file:
    for ip_line in result_ips.values():
        file.write(ip_line + "\n")

print("数据已写入 ips_latency.txt 文件")
