FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 拷贝项目文件到容器中
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口（OPC UA 和 Modbus）
EXPOSE 4840 5020

# 设置容器启动时运行的命令
CMD ["python", "main.py"]
