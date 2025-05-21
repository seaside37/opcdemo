from opcua import Client, ua
import os, sys

SERVER_URL = "opc.tcp://localhost:4840"
FILE_NODEID = "ns=2;s=AmlUpload"
LOCAL_FILE = "opas_dcn_IO.aml"
CHUNK = 64 * 1024

if not os.path.exists(LOCAL_FILE):
    sys.exit(f"找不到文件: {LOCAL_FILE}")

client = Client(SERVER_URL)
client.connect()

try:
    # 获取 AMLFile 对象节点
    aml_file_node = client.get_node("ns=2;s=AmlUpload")
    method_node = None
    for child in aml_file_node.get_children():
        bname = child.get_browse_name()
        if bname.Name == "UploadAML":
            method_node = child
            break

    if method_node is None:
        raise Exception("未找到 UploadAML 方法")

    # 读取 AML 文件内容
    with open(LOCAL_FILE, "r", encoding="utf-8") as f:
        aml_string = f.read()

    # 调用远程方法上传 AML 内容
    result = aml_file_node.call_method(method_node, aml_string)
    print("上传成功，返回值:", result)
finally:
    client.disconnect()