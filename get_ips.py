import requests
from bs4 import BeautifulSoup
import re
import os
import json

# 函数：从网站获取IP地址数据
def fetch_ips(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        ip_data = []

        if "monitor.gacjie.cn/page/cloudflare/ipv4.html" in url:
            # IP：优选地址，运营商线路：线路名称，延迟数据：往返延迟
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        ip = cols[0].text.strip()
                        isp = cols[1].text.strip()
                        latency = cols[2].text.strip()
                        latency = re.search(r'\d+', latency).group() + 'ms'
                        ip_data.append((ip, isp, latency))

        elif "cf.090227.xyz" in url:
            # IP：IP，运营商线路：线路，延迟数据：平均延迟
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    ip = cols[0].text.strip()
                    isp = cols[1].text.strip()
                    latency = cols[2].text.strip().replace('毫秒', 'ms')
                    ip_data.append((ip, isp, latency))

        elif "345673.xyz" in url:
            # IP：优选地址，运营商线路：线路名称，延迟数据：平均延迟
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    ip = cols[0].text.strip()
                    isp = cols[1].text.strip()
                    latency = cols[2].text.strip().replace('毫秒', 'ms')
                    ip_data.append((ip, isp, latency))

        elif "stock.hostmonit.com/CloudFlareYes" in url:
            # IP：IP，运营商线路：Line，延迟数据：Latency
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        ip = cols[0].text.strip()
                        isp = cols[1].text.strip()
                        latency = cols[2].text.strip().replace('毫秒', 'ms')
                        ip_data.append((ip, isp, latency))

        return ip_data

    except requests.exceptions.RequestException as e:
        print(f"从 {url} 获取数据失败: {e}")
        return []

# 函数：根据延迟和运营商过滤IP地址
def filter_ips(ip_data, max_latency=200, allowed_isps=['电信', '联通']):
    valid_ips = []
    for isp, ip, latency_str in ip_data:
        latency = re.search(r'\d+', latency_str)
        if isp in allowed_isps and latency and int(latency.group()) < max_latency:
            valid_ips.append((ip, isp, f"{latency.group()}ms"))
    return valid_ips

# 主函数：协调整个过程
def main():
    urls = [
        "https://monitor.gacjie.cn/page/cloudflare/ipv4.html",
        "https://cf.090227.xyz/",
        "https://345673.xyz/",
        "https://stock.hostmonit.com/CloudFlareYes"
    ]

    all_ip_data = []
    for url in urls:
        ip_data = fetch_ips(url)
        if ip_data:
            all_ip_data.extend(ip_data)
        else:
            print(f"跳过 {url}，获取数据失败")

    filtered_ips = filter_ips(all_ip_data)

    # 将筛选后的IP写入到ips.txt文件中
    with open('ips.txt', 'w', encoding='utf-8') as f:
        for ip, isp, latency in filtered_ips:
            f.write(f"{ip}#{isp}-{latency}\n")

if __name__ == "__main__":
    main()
