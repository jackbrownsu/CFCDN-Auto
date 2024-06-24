import requests
import os
from ipwhois import IPWhois
from bs4 import BeautifulSoup
import subprocess

# 配置
CF_API_KEY = os.getenv('CF_API_KEY')
CF_ZONE_YID = os.getenv('CF_ZONE_YID')
CF_DNS_NAME = os.getenv('CF_DNS_NAME')
FILE_PATH = 'sgfd_ips.txt'

# 第一步：从URL获取IP数据
def get_ip_data():
    url1 = 'https://raw.githubusercontent.com/ymyuuu/IPDB/main/bestproxy.txt'
    url2 = 'https://rentry.co/CF-proxyIP'

    response1 = requests.get(url1)
    ip_list1 = response1.text.splitlines()

    response2 = requests.get(url2)
    soup = BeautifulSoup(response2.text, 'html.parser')
    alibaba_ips = []
    for strong_tag in soup.find_all('strong'):
        if '🇸🇬 Singapore, Alibaba Technology Co' in strong_tag.text:
            table = strong_tag.find_next_sibling('table', class_='highlighttable')
            if table:
                for td in table.find_all('td', class_='code'):
                    ip = td.text.strip()
                    alibaba_ips.append(ip)

    # 合并IP地址列表
    ip_list = ip_list1 + alibaba_ips
    return ip_list

# 第二步：过滤新加坡IP地址，并格式化为IP#SG的形式
def filter_and_format_ips(ip_list):
    singapore_ips = []
    for ip in ip_list:
        try:
            obj = IPWhois(ip)
            results = obj.lookup_rdap()
            if results['network']['country'] == 'SG':
                singapore_ips.append(f"{ip}#SG")
        except Exception as e:
            print(f"Error processing IP {ip}: {e}")
    return singapore_ips

# 第三步：将格式化后的新加坡IP地址写入到sgfd_ips.txt文件
def write_to_file(ip_addresses):
    with open(FILE_PATH, 'w') as f:
        for ip in ip_addresses:
            f.write(ip + '\n')

# 第四步：提交sgfd_ips.txt文件到GitHub仓库
def commit_to_github():
    subprocess.run(['git', 'config', '--global', 'user.email', 'github-actions@github.com'])
    subprocess.run(['git', 'config', '--global', 'user.name', 'github-actions'])
    subprocess.run(['git', 'add', FILE_PATH])
    subprocess.run(['git', 'commit', '-m', 'Update sgfd_ips.txt with new Singapore IPs'])
    subprocess.run(['git', 'push'])

# 第五步：清除指定Cloudflare域名的所有DNS记录
def clear_dns_records():
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

# 第六步：更新Cloudflare域名的DNS记录为sgfd_ips.txt文件中的IP地址
def update_dns_records():
    with open(FILE_PATH, 'r') as f:
        ips_to_update = [line.split('#')[0].strip() for line in f]

    headers = {
        'Authorization': f'Bearer {CF_API_KEY}',
        'Content-Type': 'application/json',
    }

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

    # 第二步：过滤并格式化新加坡IP地址
    singapore_ips = filter_and_format_ips(ip_list)

    # 第三步：将格式化后的新加坡IP地址写入文件
    write_to_file(singapore_ips)

    # 第四步：提交sgfd_ips.txt文件到GitHub仓库
    commit_to_github()

    # 第五步：清除指定Cloudflare域名的所有DNS记录
    clear_dns_records()

    # 第六步：更新Cloudflare域名的DNS记录为sgfd_ips.txt文件中的IP地址
    update_dns_records()

if __name__ == "__main__":
    main()
