import requests
import re
import os
import json

# 爬取网站获取IP地址、延迟和运营商信息
def fetch_ips(url):
    response = requests.get(url)
    return re.findall(r'(\d+\.\d+\.\d+\.\d+)\#(\w+)\-(\d+ms)', response.text)

# 获取延迟低于200ms的IP地址
def filter_ips(ip_data, max_latency=200):
    valid_ips = []
    for ip, isp, latency_str in ip_data:
        latency = int(latency_str.replace('ms', ''))
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
    response = requests.get(url, headers=headers)
    records = response.json()['result']
    for record in records:
        if record['name'] == record_name:
            delete_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record['id']}"
            requests.delete(delete_url, headers=headers)

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
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

def main():
    urls = [
        "https://345673.xyz/",
        "https://cf.090227.xyz/",
        "https://stock.hostmonit.com/CloudFlareYes",
        "https://example.com/"  # 替换为实际的第四个URL
    ]
    all_ip_data = []
    for url in urls:
        all_ip_data.extend(fetch_ips(url))
    
    filtered_ips = filter_ips(all_ip_data)

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
