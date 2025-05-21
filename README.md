# opcdemo

### 镜像构建
使用以下命令构建所需的 Docker 镜像：  
`docker build -t my_opc_server ./opc_server`  
`docker build -t my_modbus_slave ./modbus_slave`  
### 项目概述
opc_server：提供 OPC UA 服务器功能，支持上传并解析 AML 文件，从而动态构建 OPC UA 地址空间结构。  
modbus_slave：作为 Modbus 从站，定时从 OPC UA 服务器中读取指定数据，并将结果写入Holding Registers，hr[0] 至 hr[2]。  
### 测试说明
使用客户端脚本将 AML 文件上传至 opc_server，并触发服务端节点结构更新：  
`python client.py`  
运行 Modbus 主站模拟脚本，轮询 modbus_slave 中的保持寄存器，验证数据同步情况：  
`python master.py` 
