## 功能

1. 从四个公开的网页获取ip数据  
https://addressesapi.090227.xyz/ip.164746.xyz  
https://addressesapi.090227.xyz/ct  
https://addressesapi.090227.xyz/CloudFlareYes  
https://ipdb.api.030101.xyz/?type=bestcf&country=true

3. 将获取的ip去重，写入到仓库中的`ips.txt`文件，该文件可用于cmliussss的cf-edge项目中的`ADDAPI`变量  
  [项目地址](https://github.com/cmliu/edgetunnel)  
  [订阅器地址](https://github.com/cmliu/WorkerVless2sub)  

4. 将`ips.txt`中的ip地址添加到cf的域名DNS记录中，该域名可用于cmliussss的cf-edge项目中的`ADD`变量

## 部署方式

> 使用`github actions`方式部署，默认每12小时自动执行一次  
> 可自行在actions的`yml`文件中修改自动运行频率  

**如何部署？**  

- fork本仓库，或[新建](https://github.com/new)一个私有库并导入本仓库的全部文件

- 依次点击`Settings`-->`Secrets and variables`-->`Secrets and variables`-->`Actions`

- 添加以下环境变量
  - `CF_API_EMAIL` = 你的cf邮箱用户名
  - `CF_API_KEY` = 你的cf API，不能使用全局API，新建一个具有dns读写权限的API。如何新建请自行谷歌
  - `CF_ZONE_ID` = 你域名的区域ID，在你的cf域名主页右下角可以找到
  - `CF_DOMAIN_NAME` = 你需要更新dns的子域名，如`cdn.yutian.xyz`

**如何修改自动运行频率？**

- 打开`.github/workflows/`文件夹中的`fetch_ips.yml`文件

- 修改第5行`- cron: '0 0/12 * * *' # 每12小时运行一次`中的参数

## 其他说明

可以添加同类型的其他网页抓取更多数据，自行在`fetch_ips.py`文件的`urls`参数中添加，  
但是必须注意：**网页内容必须是可以直接获取ip数据的直链API地址**，否则无法抓取数据。
