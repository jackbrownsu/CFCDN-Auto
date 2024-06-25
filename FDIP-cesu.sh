#!/bin/bash

# 设置语言
export LANG=zh_CN.UTF-8

# 配置目录
BASE_DIR=$(pwd)
FDIP_DIR="${BASE_DIR}/FDIP"
CFST_DIR="${BASE_DIR}/CloudflareST"

# 检查并创建所需目录
if [ ! -d "$FDIP_DIR" ]; then
    mkdir -p "$FDIP_DIR"
fi

if [ ! -d "$CFST_DIR" ]; then
    mkdir -p "$CFST_DIR"
fi

# 更新并安装依赖
install_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "$1 未安装，开始安装..."
        sudo apt-get update
        sudo apt-get install -y "$1"
        echo "$1 安装完成!"
    fi
}

install_dependency curl
install_dependency jq
install_dependency geoip-bin
install_dependency mmdb-bin

# 下载 Country.mmdb 文件
if [ ! -f "${CFST_DIR}/Country.mmdb" ]; then
    echo "Country.mmdb 文件不存在，开始下载..."
    curl -L -o "${CFST_DIR}/Country.mmdb" "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb"
    [ $? -ne 0 ] && echo "下载失败，脚本终止。" && exit 1
    echo "下载完成。"
fi

echo "============================开始下载白嫖的反代IP包============================="
download_url="https://zip.baipiao.eu.org/"
save_path="${FDIP_DIR}/txt.zip"

# 尝试下载并解压文件
for attempt in {1..10}; do
    wget "${download_url}" -O "$save_path" && break || echo "下载尝试 $attempt 失败。"
done

rm -rf "$FDIP_DIR"/*.txt
unzip "$save_path" -d "$FDIP_DIR"
sleep 1

echo "===============================合并反代IP文件==============================="
temp_file="${FDIP_DIR}/FDIPtemp.txt"
cat "${FDIP_DIR}"/*"${port}".txt > "$temp_file"

echo "===============================IP去重==============================="
awk '!seen[$0]++' "$temp_file" > "${FDIP_DIR}/FDIPtemp_unique.txt"

# 删除已下载的txt.zip及其解压出来的txt文件
rm -rf $extracted_folder $save_path

echo "=========================筛选国家代码为SG的IP地址=========================="
sg_file="${FDIP_DIR}/sg.txt"
> $sg_file

while IFS= read -r ip; do
    country_code=$(mmdblookup --file "${CFST_DIR}/Country.mmdb" --ip $ip country iso_code | awk -F '"' '{print $2}')
    if [ "$country_code" == "SG" ]; then
        echo $ip >> $sg_file
    fi
done < $temp_file

########################## 开始测速并过滤 ##########################
OUTPUT_FILE="${FDIP_DIR}/SG443FD.csv"
FINAL_OUTPUT="${FDIP_DIR}/sgcs.txt"
URL="https://spurl.api.030101.xyz/100mb"

# 下载 CloudflareSpeedTest
wget -O "${CFST_DIR}/CloudflareST.tar.gz" https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_amd64.tar.gz
tar -xzf "${CFST_DIR}/CloudflareST.tar.gz" -C "${CFST_DIR}"
chmod +x "${CFST_DIR}/CloudflareST"

# 运行速度测试
"${CFST_DIR}/CloudflareST" -tp 443 -f $sg_file -n 500 -dn 8 -tl 250 -tll 10 -o $OUTPUT_FILE -url $URL

# 过滤速度高于8ms/s的IP
awk -F, 'NR>1 && $7 > 8 {print $1 "#" $2 "-" $7 "mb/s"}' $OUTPUT_FILE > $FINAL_OUTPUT

# 提交最终的txt文件到仓库中
git add $FINAL_OUTPUT
git commit -m "Add filtered SG IPs with speed > 8mb/s"
git push origin main
