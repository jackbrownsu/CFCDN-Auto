import requests
import os
from ipwhois import IPWhois
from bs4 import BeautifulSoup

# 配置
CF_API_KEY = os.getenv('CF_API_KEY')
CF_ZONE_YID = os.getenv('CF_ZONE_YID')
CF_DNS_NAME = os.getenv('CF_DNS_NAME')
FILE_PATH = 'sgfd_ips.txt'

# 从URL获取IP数据
url1 = 'https://raw.githubusercontent.com/ymyuuu/IPDB/main/bestproxy.txt'
url2 = 'https://rentry.co/CF-proxyIP'

response1 = requests.get(url1)
ip_list1 = response1.text.splitlines()

response2 = requests.get(url2)
soup = BeautifulSoup(response2.text, 'html.parser')
alibaba_ips = []
for strong_tag in soup.find_all('strong'):
    if '🇸🇬 Singapore, Alibaba Technology Co' in strong_tag.text:
        span_tags = strong_tag.find_next_siblings('span', class_='mf')
        for span in span_tags:
            alibaba_ips.append(span.text.strip())

# 合并IP地址列表
ip_list = ip_list1 + alibaba_ips

# 过滤新加坡IP地址
singapore_ips = []
for ip in ip_list:
    try:
        obj = IPWhois(ip)
        results = obj.lookup_rdap()
        if results['network']['country'] == 'SG':
            singapore_ips.append(ip)
    except Exception as e:
        print(f"Error processing IP {ip}: {e}")

# 检查是否有新加坡IP地址
if singapore_ips:
    # 将新加坡IP地址写入文件
    with open(FILE_PATH, 'w') as f:
        for ip in singapore_ips:
            f.write(ip + '\n')

    # 更新Cloudflare DNS记录
    headers = {
        'Authorization': f'Bearer {CF_API_KEY}',
        'Content-Type': 'application/json',
    }

    # 获取现有的DNS记录
    dns_records_url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_YID}/dns_records'
    dns_records = requests.get(dns_records_url, headers=headers).json()

    # 删除旧的DNS记录
    for record in dns_records['result']:
        if record['name'] == CF_DNS_NAME:
            delete_url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_YID}/dns_records/{record["id"]}'
            requests.delete(delete_url, headers=headers)

    # 添加新的DNS记录
    for ip in singapore_ips:
        data = {
            'type': 'A',
            'name': CF_DNS_NAME,
            'content': ip,
            'ttl': 60,
            'proxied': False,
        }
        requests.post(dns_records_url, headers=headers, json=data)
