from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('127.0.0.1', port=5020)
client.connect()

result = client.read_holding_registers(0)  # 读取 Holding Register 第0位
if not result.isError():
    print("Read from slave:", result.registers)
else:
    print("Read error:", result)

client.close()
