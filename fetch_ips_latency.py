import requests
from bs4 import BeautifulSoup
import re

# 定义请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://cf.090227.xyz/',
    'Referer': 'https://stock.hostmonit.com/',
    'Referer': 'https://ip.164746.xyz/',
    'Referer': 'https://monitor.gacjie.cn/',
    'Referer': 'https://345673.xyz/'
}

# 配置多个网址
urls = [
    "https://cf.090227.xyz",
    "https://stock.hostmonit.com/CloudFlareYes",
    "https://ip.164746.xyz",
    "https://monitor.gacjie.cn/page/cloudflare/ipv4.html",
    "https://345673.xyz"
]

# 解析延迟数据的正则表达式
latency_pattern = re.compile(r'(\d+(\.\d+)?)\s*(ms|毫秒)?')

# 提取表格数据的函数
def extract_table_data(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        else:
            print(f"Failed to fetch data from {url}. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")
    return None

# 处理每个网址的数据
def process_site_data(url):
    soup = extract_table_data(url)
    if not soup:
        return []

    data = []
    if "cf.090227.xyz" in url:
        rows = soup.find_all('tr')
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 3:
                line_name = columns[0].text.strip()
                ip_address = columns[1].text.strip()
                latency_text = columns[2].text.strip()
                latency_match = latency_pattern.match(latency_text)
                if latency_match:
                    latency_value = latency_match.group(1)
                    latency_unit = 'ms'
                    data.append(f"{ip_address}#{line_name}-{latency_value}{latency_unit}")

    elif "stock.hostmonit.com" in url:
        rows = soup.find_all('tr', class_=re.compile(r'el-table row'))
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 3:
                line_name = columns[0].text.strip()
                ip_address = columns[1].find('div', class_='cell').text.strip()
                latency_text = columns[2].find('div', class_='cell').text.strip()
                latency_match = latency_pattern.match(latency_text)
                if latency_match:
                    latency_value = latency_match.group(1)
                    latency_unit = 'ms'
                    data.append(f"{ip_address}#{line_name}-{latency_value}{latency_unit}")

    elif "ip.164746.xyz" in url:
        rows = soup.find_all('td')
        for i in range(0, len(rows), 5):
            ip_address = rows[i+1].text.strip()
            latency_text = rows[i+4].text.strip()
            latency_match = latency_pattern.match(latency_text)
            if latency_match:
                latency_value = latency_match.group(1)
                latency_unit = 'ms'
                data.append(f"{ip_address}-{latency_value}{latency_unit}")
    
    elif "monitor.gacjie.cn" in url:
        rows = soup.find_all('tr')
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 7:
                line_name = columns[0].text.strip()
                ip_address = columns[1].text.strip()
                latency_text = columns[4].text.strip()
                latency_match = latency_pattern.match(latency_text)
                if latency_match:
                    latency_value = latency_match.group(1)
                    latency_unit = 'ms'
                    data.append(f"{ip_address}#{line_name}-{latency_value}{latency_unit}")
    
    elif "345673.xyz" in url:
        rows = soup.find_all('tr', class_=re.compile(r'line-cm|line-ct|line-cu'))
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 4:
                line_name = columns[0].text.strip()
                ip_address = columns[1].text.strip()
                latency_text = columns[3].text.strip()
                latency_match = latency_pattern.match(latency_text)
                if latency_match:
                    latency_value = latency_match.group(1)
                    latency_unit = 'ms'
                    data.append(f"{ip_address}#{line_name}-{latency_value}{latency_unit}")

    return data

# 主函数，处理所有网站的数据
def main():
    all_data = []
    for url in urls:
        site_data = process_site_data(url)
        all_data.extend(site_data)
    
    # 去除重复的IP地址行
    unique_data = list(set(all_data))

    # 过滤延迟数据低于100ms的行
    filtered_data = [line for line in unique_data if float(line.split('-')[-1].replace('ms', '')) < 100]

    # 写入到ips_latency.txt文件
    with open('ips_latency.txt', 'w', encoding='utf-8') as f:
        for line in filtered_data:
            f.write(line + '\n')

if __name__ == "__main__":
    main()
