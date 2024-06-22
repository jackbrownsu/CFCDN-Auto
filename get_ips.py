import requests
from bs4 import BeautifulSoup
import re
import json

# 网站 URL 列表
urls = [
    "https://monitor.gacjie.cn/page/cloudflare/ipv4.html",
    "https://stock.hostmonit.com/CloudFlareYes",
    "https://cf.090227.xyz",
    "https://345673.xyz"
]

# 请求头，模拟浏览器请求
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 存储符合条件的IP信息
ip_data = []

# 抓取数据的函数
def fetch_data(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            if "monitor.gacjie.cn" in url:
                # 解析 https://monitor.gacjie.cn/page/cloudflare/ipv4.html 网站数据
                rows = soup.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        ip = cols[0].text.strip()
                        isp = cols[1].text.strip()
                        latency = cols[2].text.strip()
                        latency = re.sub(r'毫秒', 'ms', latency)  # 将毫秒替换为ms
                        ip_data.append((ip, isp, latency))
            
            elif "stock.hostmonit.com/CloudFlareYes" in url:
                # 解析 https://stock.hostmonit.com/CloudFlareYes 网站数据
                data = json.loads(response.text)
                for entry in data:
                    ip = entry['IP']
                    isp = entry['Line']
                    latency = entry['Latency']
                    latency = re.sub(r'毫秒', 'ms', latency)  # 将毫秒替换为ms
                    ip_data.append((ip, isp, latency))
            
            elif "cf.090227.xyz" in url or "345673.xyz" in url:
                # 解析 https://cf.090227.xyz 和 https://345673.xyz 网站数据
                rows = soup.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        ip = cols[0].text.strip()
                        isp = cols[1].text.strip()
                        latency = cols[2].text.strip()
                        latency = re.sub(r'毫秒', 'ms', latency)  # 将毫秒替换为ms
                        ip_data.append((ip, isp, latency))
    
    except Exception as e:
        print(f"Failed to fetch data from {url}: {str(e)}")

# 抓取数据
for url in urls:
    fetch_data(url)

# 筛选出线路为联通或电信的IP并格式化输出到 ips.txt 文件
filtered_ips = []
for ip, isp, latency in ip_data:
    if isp in ['电信', '联通']:
        formatted_ip = f"{ip}#{isp}-{latency}"
        filtered_ips.append(formatted_ip)

# 写入 ips.txt 文件
with open('ips.txt', 'w', encoding='utf-8') as f:
    for ip_line in filtered_ips:
        f.write(ip_line + '\n')

# 输出筛选后的IP数量
print(f"Filtered IP count: {len(filtered_ips)}")
