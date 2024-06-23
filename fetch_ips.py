import os
import requests

# Cloudflare API配置信息
CF_API_KEY = os.getenv('CF_API_KEY')
CF_ZONE_ID = os.getenv('CF_ZONE_ID')
CF_DOMAIN_NAME = os.getenv('CF_DOMAIN_NAME')
CF_API_EMAIL = os.getenv('CF_API_EMAIL')

# 四个网址
urls = [
    "https://ip.164746.xyz/ipTop.html",
    "https://addressesapi.090227.xyz/ct",
    "https://addressesapi.090227.xyz/CloudFlareYes",
    "https://ipdb.api.030101.xyz/?type=bestcf&country=true"
]

# 存储抓取的数据
data = []

# 从每个网址抓取数据
for url in urls:
    response = requests.get(url)
    if response.status_code == 200:
        data.extend(response.text.split(','))  # 将逗号分隔的数据扩展到列表中
    else:
        print(f"Failed to fetch data from {url}")

# 去除重复IP
unique_data = set(data)

# 处理数据：对于没有“#”字符的行，添加“#最新优选”
processed_data = [
    ip if '#' in ip else ip + "#最新优选"
    for ip in unique_data
]

# 将处理后的数据写入ips.txt文件
with open("ips.txt", "w") as file:
    file.write("\n".join(processed_data))

# 从处理后的数据中提取IPv4地址
ipv4_addresses = [ip.split('#')[0] for ip in processed_data]

# 清空域名的所有DNS记录
def clear_dns_records():
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_API_KEY}",
        "X-Auth-Email": CF_API_EMAIL,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json().get('result', [])
        for record in records:
            delete_url = f"{url}/{record['id']}"
            delete_response = requests.delete(delete_url, headers=headers)
            if delete_response.status_code != 200:
                print(f"Failed to delete DNS record: {record['id']}")
    else:
        print("Failed to fetch DNS records")

# 添加新的IPv4地址为DNS记录
def add_dns_record(ip):
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_API_KEY}",
        "X-Auth-Email": CF_API_EMAIL,
        "Content-Type": "application/json"
    }
    data = {
        "type": "A",
        "name": CF_DOMAIN_NAME,
        "content": ip,
        "ttl": 1,
        "proxied": False
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Failed to create DNS record for IP: {ip}")

# 执行清空和添加DNS记录的操作
clear_dns_records()
for ip in ipv4_addresses:
    add_dns_record(ip)
