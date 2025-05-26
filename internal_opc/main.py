import asyncio
import threading
import logging
from pathlib import Path
from lxml import etree
from opcua import Server, Client, ua, uamethod
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock

# 日志设置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("server.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AMLParser:
    def __init__(self, aml_path):
        self.aml_path = aml_path
        self.tree = etree.parse(self.aml_path)
        self.root = self.tree.getroot()
        self.nsmap = {
            'caex': 'http://www.dke.de/CAEX',
            'aml': 'http://www.automationml.org/2009'
        }

    def parse(self):
        return {
            'InstanceHierarchy': self.parse_part('InstanceHierarchy'),
            'RoleClassLib': self.parse_part('RoleClassLib'),
            'InterfaceClassLib': self.parse_part('InterfaceClassLib'),
            'SystemUnitClassLib': self.parse_part('SystemUnitClassLib'),
            'AttributeTypeLib': self.parse_part('AttributeTypeLib')
        }

    def parse_part(self, tag):
        elems = self.root.xpath(f'.//caex:{tag}', namespaces=self.nsmap)
        return [self.parse_element(elem) for elem in elems]

    def parse_element(self, elem):
        node = {
            'tag': etree.QName(elem.tag).localname,
            'attributes': dict(elem.items()),
            'value': elem.text,
            'children': []
        }
        for child in elem:
            node['children'].append(self.parse_element(child))
        return node

class OPCUAServerBuilder:
    def __init__(self, aml_model, server, idx):
        self.server = server
        self.idx = idx
        self.aml_model = aml_model
        self.objects = self.server.get_objects_node()
        self.types = self.server.get_node(ua.ObjectIds.TypesFolder)

    def build(self):
        for part in self.aml_model:
            target_parent = self.objects if part == 'InstanceHierarchy' else self.types
            for elem in self.aml_model[part]:
                self._add_node(target_parent, elem)
        return self.server

    def _add_node(self, parent, node):
        name = node['attributes'].get('Name', node['tag'])
        obj = parent.add_object(self.idx, name)
        for child in node['children']:
            if child['tag'] == 'Attribute':
                self._add_attribute(obj, child)
            else:
                self._add_node(obj, child)
  
    def _add_attribute(self, obj, attr_node):
        name = attr_node['attributes'].get('Name', 'Attribute')
        value = attr_node['attributes'].get('Value', '')
        var = obj.add_variable(self.idx, name, value)
        var.set_writable()
        for child in attr_node['children']:
            if child['tag'] == 'Attribute':
                self._add_attribute(var, child)
            else:
                self._add_node(var, child)

# 定义方法
@uamethod
def upload_aml(parent, aml_string):
    with open("data/dcn_io.aml", "w", encoding="utf-8") as f:
        f.write(aml_string)
    logger.info("AML received and saved to dcn_io.aml")

    try:
        parser = AMLParser("data/dcn_io.aml")
        model = parser.parse()
        builder = OPCUAServerBuilder(model, server, idx)
        builder.build()
        logger.info("AML parsed and address space updated.")
        return "OK"
    except Exception as e:
        logger.exception("Failed to parse AML")
        return f"ERROR: {e}"

def start_opcua_server():
    global server, idx
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840")
    server.set_server_name("AML OPC UA Server")

    namespace_uri = "urn:demo"
    idx = server.register_namespace(namespace_uri)
    root = server.get_objects_node()
    opas_folder = root.add_folder(idx, "OPAS")

    file_nodeid = ua.NodeId("AmlUpload", idx)
    aml_file_obj = opas_folder.add_object(file_nodeid, "AMLFile", ua.ObjectIds.FileType)

    aml_file_obj.add_method(idx, "UploadAML", upload_aml, [ua.VariantType.String], [ua.VariantType.String])

    logger.info(f"[OPC UA] Server is running at opc.tcp://0.0.0.0:4840/")
    logger.info(f"[OPC UA] Method NodeId: ns={idx};s=UploadAML")

    server.start()

# 初始化 Modbus 数据存储
store = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, [0]*100))
context = ModbusServerContext(slaves=store, single=True)

OPC_SERVER_URL = "opc.tcp://localhost:4840"
OPC_NODE_ID_PV = "ns=2;i=84"
OPC_NODE_ID_LOOP1 = "ns=2;i=96"
OPC_NODE_ID_LOOP2 = "ns=2;i=108"

async def opc_to_modbus_sync():
    client = Client(OPC_SERVER_URL)
    client.connect()
    logger.info("[Modbus Slave] Connected to OPC UA server")

    try:
        while True:
            for label, nid, addr in [("PV", OPC_NODE_ID_PV, 0), ("LOOP1", OPC_NODE_ID_LOOP1, 1), ("LOOP2", OPC_NODE_ID_LOOP2, 2)]:
                try:
                    value = int(client.get_node(nid).get_value())
                    logger.info(f"[Modbus] {label} Value: {value}")
                    context[0x00].setValues(3, addr, [value])
                except Exception as e:
                    logger.warning(f"[Modbus] Failed to read {label} ({nid}): {e}")
            await asyncio.sleep(1)
    finally:
        client.disconnect()
        logger.info("[Modbus] Disconnected from OPC UA")

async def run_modbus_server():
    logger.info("[Modbus] Starting Modbus TCP server on port 5020...")
    await StartAsyncTcpServer(context, address=("0.0.0.0", 5020))

def start_opcua_thread():
    t = threading.Thread(target=start_opcua_server, daemon=True)
    t.start()
    return t

async def main():
    start_opcua_thread()
    await asyncio.sleep(2)
    await asyncio.gather(
        run_modbus_server(),
        opc_to_modbus_sync()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
        server.stop()
