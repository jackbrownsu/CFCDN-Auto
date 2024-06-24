import requests
import os
from bs4 import BeautifulSoup
import subprocess

# 配置
CF_API_KEY = os.getenv('CF_API_KEY')
CF_ZONE_YID = os.getenv('CF_ZONE_YID')
CF_DNS_NAME = os.getenv('CF_DNS_NAME')
FILE_PATH = 'sgfd_ips.txt'

# 初始化 ip_found 标志变量为 False
ip_found = False

# 第一步：从URL获取IP数据
def get_ip_data():
    url = 'https://ipdb.api.030101.xyz/?type=bestproxy&country=true'

    response = requests.get(url)
    if response.status_code == 200:
        ip_list = response.text.splitlines()
    else:
        print(f"Failed to retrieve IP data from {url}. Status code: {response.status_code}")
        ip_list = []

    return ip_list

# 第二步：过滤包含#SG的数据，并去除重复的IP地址
def filter_ips(ip_list):
    singapore_ips = set()  # 使用集合来去除重复的IP

    for ip in ip_list:
        if '#SG' in ip:
            ip_without_flag = ip.split('#')[0].strip()
            singapore_ips.add(ip_without_flag)

    return list(singapore_ips)

# 第三步：将符合条件的IP写入sgfd_ips.txt文件
def write_to_file(ip_addresses):
    with open(FILE_PATH, 'w') as f:
        for ip in ip_addresses:
            f.write(ip + '\n')

# 第四步：更新Cloudflare域名的DNS记录为sgfd_ips.txt文件中的IP地址
def update_dns_records():
    global ip_found  # 使用全局变量 ip_found

    if not ip_found:  # 如果没有找到符合条件的 IP 地址，则直接返回
        print("No Singapore IPs found. Exiting update_dns_records().")
        return

    headers = {
        'Authorization': f'Bearer {CF_API_KEY}',
        'Content-Type': 'application/json',
    }

    # 清除指定Cloudflare域名的所有DNS记录
    clear_dns_records()

    # 更新Cloudflare域名的DNS记录为sgfd_ips.txt文件中的IP地址
    dns_records_url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_YID}/dns_records'
    with open(FILE_PATH, 'r') as f:
        ips_to_update = [line.split('#')[0].strip() for line in f]

    for ip in ips_to_update:
        data = {
            'type': 'A',
            'name': CF_DNS_NAME,
            'content': ip,
            'ttl': 60,
            'proxied': False,
        }
        response = requests.post(dns_records_url, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Failed to update DNS record for {ip}. Status code: {response.status_code}")

    ip_found = True  # 设置 ip_found 为 True，表示已经找到了符合条件的 IP 地址

# 主函数：按顺序执行所有步骤
def main():
    global ip_found  # 使用全局变量 ip_found

    # 第一步：获取IP数据
    ip_list = get_ip_data()

    # 第二步：过滤并去除重复的新加坡IP地址
    singapore_ips = filter_ips(ip_list)
    
    # 如果没有找到符合条件的新加坡IP，则终止后续动作
    if not singapore_ips:
        print("No Singapore IPs found. Exiting.")
        return

    # 第三步：将格式化后的新加坡IP地址写入文件
    write_to_file(singapore_ips)

    # 第四步：更新Cloudflare域名的DNS记录为sgfd_ips.txt文件中的IP地址
    update_dns_records()

if __name__ == "__main__":
    main()

# 在此处可以根据 ip_found 的值来判断是否执行后续的 GitHub Actions 步骤
if ip_found:
    subprocess.run(['python', 'commit_push.py'])  # 例如执行提交和推送到仓库的脚本
