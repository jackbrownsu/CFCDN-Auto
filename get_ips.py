import requests
from bs4 import BeautifulSoup
import re
import os
import json

# 获取IP地址、运营商线路和往返延迟数据
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
                        latency = cols[2].text.strip().replace('毫秒', 'ms')
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
        print(f"Failed to fetch data from {url}: {e}")
        return []

# 获取延迟低于200ms的IP地址，且排除移动运营商
def filter_ips(ip_data, max_latency=200):
    valid_ips = []
    for isp, ip, latency_str in ip_data:
        if isp in ['电信', '联通']:
            latency = re.search(r'\d+', latency_str)
            if latency and int(latency.group()) < max_latency:
                valid_ips.append((ip, isp, f"{latency.group()}ms"))
    return valid_ips

# 写入到ips.txt文件
def write_to_file(filtered_ips):
    with open('ips.txt', 'w') as f:
        for ip, isp, latency in filtered_ips:
            f.write(f"{ip}#{isp}-{latency}\n")

# 解析到Cloudflare指定域名DNS记录
def update_cloudflare_dns(filtered_ips):
    cf_domain_mapping = {
        '电信': 'ct.yutian.us.kg',
        '联通': 'cu.yutian.us.kg'
    }
    
    for ip, isp, latency in filtered_ips:
        if isp in cf_domain_mapping:
            domain = cf_domain_mapping[isp]
            try:
                # 删除原有的DNS记录（假设通过API或其他方式进行删除）
                print(f"Deleting existing DNS records for {domain}")
                
                # 添加新的DNS记录
                print(f"Adding DNS record: {ip} -> {domain}")
                # 这里应该是实际添加DNS记录的代码，可以使用Cloudflare的API进行添加操作
                # 示例：requests.post('Cloudflare API URL', json={'ip': ip, 'domain': domain})
                
            except Exception as e:
                print(f"Failed to update DNS for {domain}: {e}")

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
            print(f"Skipping {url} due to fetch failure")

    # 调试信息
    print("All IP data fetched:")
    for ip_info in all_ip_data:
        print(ip_info)

    filtered_ips = filter_ips(all_ip_data)

    # 调试信息
    print("Filtered IPs:")
    for ip_info in filtered_ips:
        print(ip_info)

    # 写入到ips.txt文件
    write_to_file(filtered_ips)

    # 更新Cloudflare的DNS记录
    update_cloudflare_dns(filtered_ips)

if __name__ == "__main__":
    main()
