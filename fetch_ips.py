import requests

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

# 去除重复IP并在每行末尾添加“#最新优选”
unique_data = set(data)
processed_data = [ip + " #最新优选" for ip in unique_data]

# 将处理后的数据写入ips.txt文件
with open("ips.txt", "w") as file:
    file.write("\n".join(processed_data))
