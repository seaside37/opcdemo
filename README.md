# opcdemo

## 镜像构建
使用以下命令构建所需的 Docker 镜像：
`docker build -t my_opc_server ./opc_server`
`docker build -t my_modbus_slave ./modbus_slave`

## 解释
opc_server中提供了一个方法来传输文件，并能通过解析aml文件得到opc服务器的结构
modbus_slave能够从opc_server中读取数据，并提供一个从站的能力，数据寄存在hr[0]-hr[2]中

## 测试
client通过调用opc_server中的方法来传输aml文件，通过运行python client.py使得opc服务器中发生更新
modbus_master从modbus_slave中轮询数据，通过运行python modbus_master.py得到指定的数据
让这段readme更专业一些
