import requests
import os
from urllib.parse import quote
import subprocess

# 配置
CF_API_KEY = os.getenv('CF_API_KEY')
CF_ZONE_YID = os.getenv('CF_ZONE_YID')
CF_DNS_NAME = os.getenv('CF_DNS_NAME')
FILE_PATH = 'sgfd_ips.txt'

# 第一步：从URL获取IP数据
def get_ip_data():
    url = 'https://ipdb.api.030101.xyz/?type=bestproxy&country=true'

    response = requests.get(url)
    if response.status_code == 200:
        ip_list = response.json()['data']
        singapore_ips = [ip['ip'] for ip in ip_list if '#SG' in ip['ip']]
        return singapore_ips
    else:
        print(f"Failed to fetch IP data from {url}")
        return []

# 第二步：去重并写入到sgfd_ips.txt文件
def write_to_file(ip_addresses):
    unique_ips = list(set(ip_addresses))  # 去除重复IP
    with open(FILE_PATH, 'w') as f:
        for ip in unique_ips:
            f.write(ip + '\n')

# 清除指定Cloudflare域名的所有DNS记录
def clear_dns_records():
    headers = {
        'Authorization': f'Bearer {CF_API_KEY}',
        'Content-Type': 'application/json',
    }

    dns_records_url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_YID}/dns_records'
    dns_records = requests.get(dns_records_url, headers=headers).json()

    # 删除旧的DNS记录
    for record in dns_records['result']:
        if record['name'] == CF_DNS_NAME:
            delete_url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_YID}/dns_records/{record["id"]}'
            requests.delete(delete_url, headers=headers)

# 第三步：更新Cloudflare域名的DNS记录为sgfd_ips.txt文件中的IP地址
def update_dns_records():
    with open(FILE_PATH, 'r') as f:
        ips_to_update = [line.split('#')[0].strip() for line in f]

    headers = {
        'Authorization': f'Bearer {CF_API_KEY}',
        'Content-Type': 'application/json',
    }

    # 更新DNS记录
    dns_records_url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_YID}/dns_records'
    for ip in ips_to_update:
        data = {
            'type': 'A',
            'name': CF_DNS_NAME,
            'content': ip,
            'ttl': 60,
            'proxied': False,
        }
        requests.post(dns_records_url, headers=headers, json=data)

# 主函数：按顺序执行所有步骤
def main():
    # 第一步：获取IP数据
    ip_list = get_ip_data()

    # 第二步：将去重后的新加坡IP地址写入文件
    write_to_file(ip_list)

    # 如果没有符合条件的新加坡IP，则终止后续动作
    if not ip_list:
        print("No Singapore IPs found. Exiting.")
        return

    # 第三步：清除指定Cloudflare域名的所有DNS记录
    clear_dns_records()

    # 第四步：更新Cloudflare域名的DNS记录为sgfd_ips.txt文件中的IP地址
    update_dns_records()

if __name__ == "__main__":
    main()
