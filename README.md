## 感谢
[snowfal1](https://github.com/snowfal1/CloudflareCDNFission)

## 使用
<details>
  <summary>点击展开</summary>
  
- 在 `Fission_ip.txt` 中填入至少一个反代IP
  
- Settings: `Actions` --> `General` --> `Read and write permissions`，保存
  
- Actions：`All workflows` --> `Run CloudflareCDN` --> `Run workflow`，等待运行完成
  
- `Fission_domain.txt`文件：自动生成的域名
  
- `Fission_ip2cc.txt`文件：自动生成的IP，可以作为cm节点脚本的ADDAPI使用，raw地址前加`https://github.yutian81.top/`
  
  - 示例：`https://github.yutian81.top/yutian81/CFCDN-Auto/main/Fission_ip2cc.txt`
    
- \.github\workflows\run.yml文件中可以设置自动运行：`# schedule`和`# - cron: '0 0 * * 3'`去掉`#`号，修改计划

</details>
