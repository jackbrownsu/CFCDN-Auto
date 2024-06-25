export LANG=zh_CN.UTF-8
# 选择代理，不能拉取依赖或拉取依赖慢时用https://dl.houyitfg.icu/proxy/
proxy="https://dl.houyitfg.icu/proxy/"
# 先择域（31898和45102）都要就留空
asn=""
# 端口，都要就留空
port="443"
# 是否验证反代并保留纯净IP，true，false
scip="true"
# 识别后的结果文件夹名称
IP="FDIP"
###################################################################################################
# 检查并安装依赖
# 选择客户端 CPU 架构
archAffix(){
    case "$(uname -m)" in
        i386 | i686 ) echo 'i386' ;;
        x86_64 | amd64 ) echo 'amd64' ;;
        armv8 | arm64 | aarch64 ) echo 'arm64' ;;
		arm ) echo 'arm' ;;
        * ) red "不支持的CPU架构!" && exit 1 ;;
    esac
}

update_gengxinzhi=0
apt_update() {
    if [ "$update_gengxinzhi" -eq 0 ]; then

		if grep -qi "alpine" /etc/os-release; then
			apk update
		elif grep -qi "openwrt" /etc/os-release; then
			opkg update
			#openwrt没有安装timeout
			opkg install coreutils-timeout
		elif grep -qi "ubuntu\|debian" /etc/os-release; then
			sudo apt-get update
		else
			echo "$(uname) update"
		fi
 
        update_gengxinzhi=$((update_gengxinzhi + 1))
    fi
}

apt_install() {
    if ! command -v "$1" &> /dev/null; then
        echo "$1 未安装，开始安装..."
        apt_update
        
	if grep -qi "alpine" /etc/os-release; then
		apk add $1
	elif grep -qi "openwrt" /etc/os-release; then
		opkg install $1
	elif grep -qi "ubuntu\|debian" /etc/os-release; then
		sudo apt-get install $1 -y
	elif grep -qi "centos\|red hat\|fedora" /etc/os-release; then
		sudo yum install $1 -y
	else
		echo "未能检测出你的系统：$(uname)，请自行安装$1。"
		exit 1
	fi
 
        echo "$1 安装完成!"
    fi
}

apt_install curl  # 安装curl
apt_install jq

# 检测是否已经安装了geoiplookup
if ! command -v geoiplookup &> /dev/null; then
    echo "geoiplookup Not installed, start installation..."
    apt_update
    apt_install geoip-bin -y
    echo "geoiplookup The installation is complete!"
fi

if ! command -v mmdblookup &> /dev/null; then
    echo "mmdblookup Not installed, start installation..."
    apt_update
    apt_install mmdb-bin
    echo "mmdblookup The installation is complete!"
fi

# 检测Country.mmdb文件是否存在
if [ ! -f "Country.mmdb" ]; then
    echo "The file Country.mmdb does not exist. downloading..."
    
    # 使用curl命令下载文件
    curl -L -o Country.mmdb "${proxy}https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb"
    
    # 检查下载是否成功
    if [ $? -eq 0 ]; then
        echo "Download completed."
    else
        echo "Download failed. The script terminates."
        exit 1
    fi
fi

echo ============================开始下载白嫖的反代IP包================================
# 定义下载链接和保存路径
download_url="${proxy}https://zip.baipiao.eu.org/"
save_path="/txt.zip"
extracted_folder="/FDIP-TXT"  # 解压后的文件夹路径
###################################################################################################
# 定义最大尝试次数
max_attempts=10
current_attempt=1
###################################################################################################
# 循环尝试下载
while [ $current_attempt -le $max_attempts ]
do
    # 下载文件
    wget "${download_url}" -O $save_path

    # 检查是否下载成功
    if [ $? -eq 0 ]; then
        break
    else
        echo "Download attempt $current_attempt failed."
        current_attempt=$((current_attempt+1))
    fi
done
# 删除原来的txt文件夹内容
rm -rf $extracted_folder/*
# 解压文件
unzip $save_path -d $extracted_folder
sleep 1 > /dev/null

echo ===============================合并反代IP文件=====================================
rm -rf "${IP}"
sleep 1 > /dev/null
mkdir "${IP}"
mkdir "${IP}/C"
temp_file="${IP}/FDIPtemp.txt"
cat $extracted_folder/${asn}*${port}.txt > $temp_file
echo "IP包下载处理成功"
sleep 1 > /dev/null

echo ===================================IP去重=========================================
# 指定目录
DIRECTORY="${IP}"

# 遍历指定目录中的所有文本文件
find "$DIRECTORY" -type f -name "*.txt" -print0 | while IFS= read -r -d '' file; do
    # 创建临时文件
    tempfile=$(mktemp)
    
    # 使用awk去除重复行，并将结果写入临时文件
    awk '!seen[$0]++' "$file" > "$tempfile"
    
    # 检查临时文件是否为空，如果为空则不覆盖原文件
    if [ -s "$tempfile" ]; then
        # 使用mv命令将临时文件重命名为原文件，覆盖原文件
        mv "$tempfile" "$file"
    else
        # 如果临时文件为空，则删除它
        rm "$tempfile"
    fi
done

#######################################验证反代IP及纯净度###########################################
FDIP="${IP}/FDIP.txt"
FDIPC="${IP}/FDIPC.txt"
> $FDIP
> $FDIPC

if [ "$scip" = "true" ]; then
echo 已选验证反代IP及纯净度
echo ========================验证反代IP及纯净度，保留纯净IP===========================
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
done < "$temp_file"

elif [ "$scip" = "false" ]; then
cat $temp_file > $FDIP
echo 未选验证反代IP及纯净度
fi
echo ==============================开始识别IP所在地===================================
while read -r line; do
    ip=$(echo $line | cut -d ' ' -f 1)  # 提取IP地址部分
	result=$(mmdblookup --file Country.mmdb --ip $ip country iso_code)
	country_code=$(echo $result | awk -F '"' '{print $2}')
	echo $ip >> "${IP}/${country_code}-${port}.txt"  # 写入对应的国家文件
done < $FDIP

while read -r line; do
    ip=$(echo $line | cut -d ' ' -f 1)  # 提取IP地址部分
	result=$(mmdblookup --file Country.mmdb --ip $ip country iso_code)
	country_code=$(echo $result | awk -F '"' '{print $2}')
	echo $ip >> "${IP}/C/${country_code}-${port}.txt"  # 写入对应的国家文件
done < $FDIPC

rm -rf $extracted_folder
rm -rf $save_path

echo "IP所在地识别完毕，结果已储存在${IP}文件夹中，纯净IP文件夹为C，未识别前的文件为FDIPtemp.txt"
