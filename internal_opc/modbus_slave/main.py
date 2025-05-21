import asyncio
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from opcua import Client
import os

# 初始化 Modbus 寄存器数据块
store = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, [0]*100))
context = ModbusServerContext(slaves=store, single=True)

# OPC UA 地址和目标节点
OPC_SERVER_URL = os.getenv("OPC_SERVER_URL", "opc.tcp://opc_server:4840")
# OPC_SERVER_URL = "opc.tcp://localhost:4840"
OPC_NODE_ID_PV = "ns=2;i=84"
OPC_NODE_ID_LOOP1 = "ns=2;i=96"
OPC_NODE_ID_LOOP2 = "ns=2;i=108"

# 定期从 OPC UA 获取值，并写入 Modbus 寄存器
async def opc_to_modbus_sync():
    client = Client(OPC_SERVER_URL)
    client.connect()
    print("Connected to OPC UA server")

    try:
        while True:
            read_value = lambda nid: int(client.get_node(nid).get_value())

            for label, nid, addr in [("PV", OPC_NODE_ID_PV, 0), ("LOOP1", OPC_NODE_ID_LOOP1, 1), ("LOOP2", OPC_NODE_ID_LOOP2, 2)]:
                value = read_value(nid)
                print(f"{label} Value:", value)
                context[0x00].setValues(3, addr, [value])

            await asyncio.sleep(1)
    except Exception as e:
        print("OPC-UA Error:", e)
    finally:
        client.disconnect()
        print("Disconnected from OPC UA")

# 启动 Modbus TCP 服务器
async def run_server():
    print("Starting Modbus TCP server on port 5020...")
    await StartAsyncTcpServer(context, address=("0.0.0.0", 5020))

# 启动所有任务
async def main():
    await asyncio.gather(
        run_server(),
        opc_to_modbus_sync(),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nModbus server stopped by user.")
