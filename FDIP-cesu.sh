#!/bin/bash

# 设置语言
export LANG=zh_CN.UTF-8

# 配置目录
BASE_DIR=$(pwd)
FDIP_DIR="${BASE_DIR}/FDIP"
CFST_DIR="${BASE_DIR}/CloudflareST"
SG_FILE="${FDIP_DIR}/sg.txt"
OUTPUT_FILE="${FDIP_DIR}/SG443FD.csv"
FINAL_OUTPUT="${FDIP_DIR}/sgcs.txt"
URL="https://spurl.api.030101.xyz/100mb"
SAVE_PATH="${FDIP_DIR}/txt.zip"

# 创建所需目录
mkdir -p "${FDIP_DIR}"
mkdir -p "${CFST_DIR}"

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
install_dependency unzip

# 下载 txt.zip 文件
echo "============================开始下载txt.zip============================="
download_url="https://zip.baipiao.eu.org/"
wget "${download_url}" -O "${SAVE_PATH}"
if [ $? -ne 0 ]; then
    echo "下载失败，脚本终止。"
    exit 1
fi

# 解压 txt.zip 文件并保留只有45102-1-443.txt和31898-1-443.txt，删除其他文件
echo "===============================解压和合并文件==============================="
unzip "${SAVE_PATH}" -d "${FDIP_DIR}"

# 删除除了45102-1-443.txt和31898-1-443.txt之外的所有文件
find "${FDIP_DIR}" -type f ! \( -name '45102-1-443.txt' -o -name '31898-1-443.txt' \) -delete

# 合并文件
cat "${FDIP_DIR}/45102-1-443.txt" "${FDIP_DIR}/31898-1-443.txt" > "${FDIP_DIR}/all.txt"
awk '!seen[$0]++' "${FDIP_DIR}/all.txt" > "${FDIP_DIR}/all_unique.txt"

# 清空或创建空的sg.txt文件
> $SG_FILE

echo "=========================筛选国家代码为SG的IP地址=========================="
while IFS= read -r ip; do
    country_code=$(curl -s "https://ipapi.co/$ip/country/" | tr -d '[:space:]')
    if [ "$country_code" == "SG" ]; then
        echo $ip >> $SG_FILE
    fi
done < "${FDIP_DIR}/all_unique.txt"

# 输出sg.txt文件中的内容，用于调试
echo "SG IPs:"
cat $SG_FILE

echo "============================开始测速并筛选==============================="
# 下载 CloudflareSpeedTest
if [ ! -f "${CFST_DIR}/CloudflareST.tar.gz" ]; then
    echo "CloudflareST文件不存在，开始下载..."
    wget -O "${CFST_DIR}/CloudflareST.tar.gz" https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_amd64.tar.gz
    tar -xzf "${CFST_DIR}/CloudflareST.tar.gz" -C "${CFST_DIR}"
    chmod +x "${CFST_DIR}/CloudflareST"
fi

# 运行速度测试
"${CFST_DIR}/CloudflareST" -tp 443 -f $SG_FILE -n 500 -dn 8 -tl 250 -tll 10 -o $OUTPUT_FILE -url $URL

# 过滤速度高于6 mb/s的IP
awk -F, 'NR>1 && $7 > 6 {print $1 "#" $2 "-" $7 "mb/s"}' $OUTPUT_FILE > $FINAL_OUTPUT

echo "测速完成，速度超过6 mb/s的IP地址已保存到sgcs.txt文件中。"
