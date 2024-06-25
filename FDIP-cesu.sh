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

# 尝试下载文件
for attempt in {1..10}; do
    wget "${download_url}" -O $save_path && break || echo "下载尝试 $attempt 失败。"
done

# 解压txt.zip文件
unzip $save_path -d $FDIP_DIR

# 删除除了45102-1-443.txt和31898-1-443.txt之外的所有文件
find "${FDIP_DIR}" -type f ! \( -name '45102-1-443.txt' -o -name '31898-1-443.txt' \) -delete

# 合并文件并去重
cat "${FDIP_DIR}/45102-1-443.txt" "${FDIP_DIR}/31898-1-443.txt" > "${FDIP_DIR}/all.txt"
awk '!seen[$0]++' "${FDIP_DIR}/all.txt" > "${FDIP_DIR}/all_unique.txt"

# 删除已下载的txt.zip文件
rm $save_path

echo "=========================筛选国家代码为SG的IP地址=========================="
sg_file="${FDIP_DIR}/sg.txt"
> $sg_file  # 清空或创建空的sg.txt文件

while IFS= read -r ip; do
    country_code=$(mmdblookup --file "${CFST_DIR}/Country.mmdb" --ip $ip country iso_code | awk -F '"' '{print $2}')
    if [ "$country_code" == "SG" ]; then
        echo $ip >> $sg_file
    fi
done < "${FDIP_DIR}/all_unique.txt"

# 输出sg.txt文件中的内容，用于调试
echo "SG IPs:"
cat $sg_file

########################## 开始测速并过滤 ##########################
OUTPUT_FILE="${FDIP_DIR}/SG443FD.csv"
FINAL_OUTPUT="${FDIP_DIR}/sgcs.txt"
URL="https://spurl.api.030101.xyz/100mb"

# 下载 CloudflareSpeedTest，仅在CloudflareST.tar.gz不存在时下载
if [ ! -f "${CFST_DIR}/CloudflareST.tar.gz" ]; then
    wget -O "${CFST_DIR}/CloudflareST.tar.gz" https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_amd64.tar.gz
fi

# 设置权限和解压，仅在CloudflareST文件夹中CloudflareST目录不存在时执行
if [ ! -d "${CFST_DIR}/CloudflareST" ]; then
    tar -xzf "${CFST_DIR}/CloudflareST.tar.gz" -C "${CFST_DIR}"
    chmod +x "${CFST_DIR}/CloudflareST/CloudflareST"
fi

# 运行速度测试
"${CFST_DIR}/CloudflareST" -tp 443 -f $sg_file -n 500 -dn 8 -tl 250 -tll 10 -o $OUTPUT_FILE -url $URL

# 过滤速度高于8m/s的IP
awk -F, 'NR>1 && $7 > 8 {print $1 "#" $2 "-" $7 "m/s"}' "$OUTPUT_FILE" > "${FDIP_DIR}/sgcs.txt"

# 提交最终的txt文件到仓库中
git add $FINAL_OUTPUT
git commit -m "Add filtered SG IPs with speed > 8mb/s"
git push origin main
