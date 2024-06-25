#!/bin/bash

# 设置语言和代理
export LANG=zh_CN.UTF-8
proxy="https://dl.houyitfg.icu/proxy/"
asn=""
port="443"
scip="true"
IP="FDIP"

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
if [ ! -f "Country.mmdb" ]; then
    echo "Country.mmdb 文件不存在，开始下载..."
    curl -L -o Country.mmdb "${proxy}https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb"
    [ $? -ne 0 ] && echo "下载失败，脚本终止。" && exit 1
    echo "下载完成。"
fi

echo "============================开始下载白嫖的反代IP包============================="
download_url="${proxy}https://zip.baipiao.eu.org/"
save_path="/txt.zip"
extracted_folder="/FDIP-TXT"

# 尝试下载并解压文件
for attempt in {1..10}; do
    wget "${download_url}" -O $save_path && break || echo "下载尝试 $attempt 失败。"
done

rm -rf $extracted_folder/*
unzip $save_path -d $extracted_folder
sleep 1

echo "===============================合并反代IP文件==============================="
rm -rf "${IP}"
mkdir -p "${IP}/C"
temp_file="${IP}/FDIPtemp.txt"
cat $extracted_folder/${asn}*${port}.txt > $temp_file

echo "===============================IP去重==============================="
awk '!seen[$0]++' $temp_file > "${IP}/FDIPtemp_unique.txt"

#######################################验证反代IP及纯净度###########################################
FDIP="${IP}/FDIP.txt"
FDIPC="${IP}/FDIPC.txt"
> $FDIP
> $FDIPC

if [ "$scip" = "true" ]; then
    echo "已选验证反代IP及纯净度"
    while IFS= read -r ip; do
        PAGE_CONTENT=$(curl -s --connect-timeout 1 "http://$ip")
        if echo "$PAGE_CONTENT" | grep -q "1003"; then
            echo "$ip" >> "$FDIP"
            echo "得到一个反代IP[$ip]"
            if curl -s --connect-timeout 1 "https://scamalytics.com/ip/$ip" | grep -q '"risk":"low"'; then
                echo "$ip" >> "$FDIPC"
                echo "此反代IP纯净[$ip]"
            fi
        fi
    done < "${IP}/FDIPtemp_unique.txt"
else
    cat "${IP}/FDIPtemp_unique.txt" > $FDIP
    echo "未选验证反代IP及纯净度"
fi

echo "==============================开始识别IP所在地==============================="
while read -r ip; do
    country_code=$(mmdblookup --file Country.mmdb --ip $ip country iso_code | awk -F '"' '{print $2}')
    echo $ip >> "${IP}/${country_code}-${port}.txt"
done < $FDIP

while read -r ip; do
    country_code=$(mmdblookup --file Country.mmdb --ip $ip country iso_code | awk -F '"' '{print $2}')
    echo $ip >> "${IP}/C/${country_code}-${port}.txt"
done < $FDIPC

rm -rf $extracted_folder $save_path

echo "IP所在地识别完毕，结果已储存在${IP}文件夹中，纯净IP文件夹为C"

########################## 开始测速并过滤 ##########################
SG_FILE="${IP}/C/SG-443.txt"
OUTPUT_FILE="SG443FD.csv"
FINAL_OUTPUT="SG_filtered.txt"
URL="https://spurl.api.030101.xyz/100mb"

# 下载 CloudflareSpeedTest
wget -O CloudflareST.tar.gz https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_amd64.tar.gz
tar -xzf CloudflareST.tar.gz
chmod +x CloudflareST

# 运行速度测试
./CloudflareST -tp 443 -f $SG_FILE -n 500 -dn 8 -tl 250 -tll 10 -o $OUTPUT_FILE -url $URL

# 过滤速度高于8ms/s的IP
awk -F, 'NR>1 && $7 > 8 {print $1 "#" $2 "-" $7 "mb/s"}' $OUTPUT_FILE > $FINAL_OUTPUT

# 提交最终的txt文件到仓库中
git add $FINAL_OUTPUT
git commit -m "Add filtered SG IPs with speed > 8mb/s"
git push origin main
