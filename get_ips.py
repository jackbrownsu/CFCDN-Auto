import requests
from bs4 import BeautifulSoup
import re
import os
import json
import time

# 获取IP地址、运营商线路和延迟数据
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
                        ip_data.append((ip, isp, latency))

        elif "cf.090227.xyz" in url:
            # IP：IP，运营商线路：线路，延迟数据：平均延迟
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    ip = cols[0].text.strip()
                    isp = cols[1].text.strip()
                    latency = cols[2].text.strip()
                    ip_data.append((ip, isp, latency))

        elif "345673.xyz" in url:
            # IP：优选地址，运营商线路：线路名称，延迟数据：平均延迟
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    ip = cols[0].text.strip()
                    isp = cols[1].text.strip()
                    latency = cols[2].text.strip()
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
                        latency = cols[2].text.strip()
                        ip_data.append((ip, isp, latency))

        return ip_data

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data from {url}: {e}")
        return []

# 获取延迟低于200ms的IP地址，且排除移动运营商
def filter_ips(ip_data, max_latency=200):
    valid_ips = []
    for ip, isp, latency_str in ip_data:
        latency = int(re.search(r'\d+', latency_str).group())  # 提取数字部分作为延迟数值
        if latency < max_latency and isp in ['电信', '联通']:
            valid_ips.append((ip, isp, latency_str))
    return valid_ips

# 删除现有的特定DNS记录
def delete_existing_dns_records(record_name, zone_id, api_key, api_email):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        'X-Auth-Email': api_email,
        'X-Auth-Key': api_key,
        'Content-Type': 'application/json',
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        records = response.json()['result']
        for record in records:
            if record['name'] == record_name:
                delete_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record['id']}"
                requests.delete(delete_url, headers=headers)
    except requests.exceptions.RequestException as e:
        print(f"Failed to delete DNS records for {record_name}: {e}")

# 更新DNS记录
def update_dns_record(ip, record_name, zone_id, api_key, api_email):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        'X-Auth-Email': api_email,
        'X-Auth-Key': api_key,
        'Content-Type': 'application/json',
    }
    data = {
        "type": "A",
        "name": record_name,
        "content": ip,
        "ttl": 1,
        "proxied": False
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to update DNS record for {record_name}: {e}")
        return None

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

    cf_api_key = os.getenv('CF_API_KEY')
    cf_api_email = os.getenv('CF_API_EMAIL')
    cf_zone_id = os.getenv('CF_ZONE_ID')
    
    # 先删除特定子域名的DNS记录
    delete_existing_dns_records('ct.yutian.us.kg', cf_zone_id, cf_api_key, cf_api_email)
    delete_existing_dns_records('cu.yutian.us.kg', cf_zone_id, cf_api_key, cf_api_email)

    with open('ips.txt', 'w') as f:
        for ip, isp, latency in filtered_ips:
            if isp == '电信':
                record_name = 'ct.yutian.us.kg'
            elif isp == '联通':
                record_name = 'cu.yutian.us.kg'
            else:
                continue  # 跳过非电信或联通的IP

            f.write(f"{ip}#{isp}-{latency}\n")
            
            # 更新新的DNS记录
            update_dns_record(ip, record_name, cf_zone_id, cf_api_key, cf_api_email)

if __name__ == "__main__":
    main()
