\documentclass{article}
\usepackage[a4paper, margin=1in]{geometry}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{titling}

\title{OPCDemo 项目说明}
\author{}
\date{}

\definecolor{codegray}{gray}{0.95}
\lstset{
    backgroundcolor=\color{codegray},
    basicstyle=\ttfamily\small,
    breaklines=true,
    frame=single,
    language=bash,
    captionpos=b
}

\begin{document}

\maketitle

\section*{镜像构建}

使用以下命令构建所需的 Docker 镜像：

\begin{lstlisting}
docker build -t my_opc_server ./opc_server
docker build -t my_modbus_slave ./modbus_slave
\end{lstlisting}

\section*{项目概述}

本项目旨在模拟 OPC UA 与 Modbus 协议之间的数据交互流程，主要包含两个模块：

\begin{itemize}
    \item \textbf{opc\_server}：提供 OPC UA 服务器功能，支持上传并解析 AML 文件，从而动态构建 OPC UA 地址空间结构。
    \item \textbf{modbus\_slave}：作为 Modbus 从站，定时从 OPC UA 服务器中读取指定数据，并将结果写入自身保持寄存器（Holding Registers）\texttt{hr[0]} 至 \texttt{hr[2]}。
\end{itemize}

\section*{功能说明}

\begin{itemize}
    \item \textbf{AML 文件传输与解析}：\texttt{opc\_server} 提供一个用于接收 AML 文件的接口。客户端可上传 AML 文件，服务器解析后根据其内容自动生成 OPC UA 节点结构。
    \item \textbf{OPC UA 到 Modbus 数据桥接}：\texttt{modbus\_slave} 通过 OPC UA 协议从 \texttt{opc\_server} 读取数据，并将其映射至 Modbus 寄存器，提供 Modbus TCP 接口供主站访问。
\end{itemize}

\section*{测试说明}

\subsection*{步骤 1：上传 AML 文件并更新 OPC UA 结构}

使用客户端脚本将 AML 文件上传至 \texttt{opc\_server}，并触发服务端节点结构更新：

\begin{lstlisting}[language=Python]
python client.py
\end{lstlisting}

\subsection*{步骤 2：读取 Modbus 从站中的数据}

运行 Modbus 主站模拟脚本，轮询 \texttt{modbus\_slave} 中的保持寄存器，验证数据同步情况：

\begin{lstlisting}[language=Python]
python modbus_master.py
\end{lstlisting}

\section*{扩展建议}

如需进一步扩展或集成该系统，可考虑以下内容：

\begin{itemize}
    \item 添加日志记录与异常处理机制；
    \item 引入前端界面用于上传 AML 文件与可视化数据；
    \item 使用 Docker Compose 实现一键部署与容器编排；
    \item 支持多种工业数据源或协议的扩展（如 MQTT、OPC UA PubSub 等）。
\end{itemize}

\end{document}
