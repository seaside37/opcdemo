from pathlib import Path
from lxml import etree
from opcua import Server, ua, uamethod

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
        # 分块解析五个部分
        return {
            'InstanceHierarchy': self.parse_part('InstanceHierarchy'),
            'RoleClassLib': self.parse_part('RoleClassLib'),
            'InterfaceClassLib': self.parse_part('InterfaceClassLib'),
            'SystemUnitClassLib': self.parse_part('SystemUnitClassLib'),
            'AttributeTypeLib': self.parse_part('AttributeTypeLib')
        }

    def parse_part(self, tag):
        # 通用解析入口: 根据标签找到对应元素
        elems = self.root.xpath(f'.//caex:{tag}', namespaces=self.nsmap)
        result = []
        for elem in elems:
            result.append(self.parse_element(elem))
        return result
    
    def parse_element(self, elem):
        # 递归遍历元素及其所有子元素，保留层级和属性
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
        # 根据aml_model创建节点对象
        for part in self.aml_model:
            target_parent = (self.objects if part == 'InstanceHierarchy' else self.types)
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


# 定义方法：接收 AML 字符串并保存为文件
@uamethod
def upload_aml(parent, aml_string):
    with open("dcn_io.aml", "w", encoding="utf-8") as f:
        f.write(aml_string)
    print("AML received and saved to dcn_io.aml")

    base_dir = Path(__file__).resolve().parent
    aml_path = base_dir / "dcn_io.aml"
    try:
        parser = AMLParser("dcn_io.aml")
        model = parser.parse()
        builder = OPCUAServerBuilder(model, server, idx)
        builder.build()
        print("AML parsed and address space updated.")
        return "OK"
    except Exception as e:
        print("Failed to parse AML:", e)
        return f"ERROR: {e}"


# 创建 OPC UA 服务器
server = Server()
server.set_endpoint("opc.tcp://0.0.0.0:4840")
server.set_server_name("AML OPC UA Server")

namespace_uri = "urn:demo"
idx = server.register_namespace(namespace_uri)
root = server.get_objects_node()
opas_folder = root.add_folder(idx, "OPAS")

# 创建 AML 文件对象（类型为 FileType）
file_nodeid = ua.NodeId("AmlUpload", idx)
aml_file_obj = opas_folder.add_object(
    file_nodeid,
    "AMLFile",
    ua.ObjectIds.FileType
)

# 添加 UploadAML 方法
aml_file_obj.add_method(
    idx,
    "UploadAML",
    upload_aml,
    [ua.VariantType.String],
    [ua.VariantType.String]
)

print(f"OPC UA Server is running at opc.tcp://0.0.0.0:4840/")
print(f"Namespace index: {idx}")
print(f"Method NodeId: ns={idx};s=UploadAML")

server.start()

try:
    while True:
        pass
except KeyboardInterrupt:
    print("Stopping server...")
    server.stop()
