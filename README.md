# ZIM-RAG 本地知识库问答系统

基于 ZIM 文件和本地大语言模型 (Ollama) 的检索增强生成 (RAG) 系统。

## 项目背景

随着离线知识库（如维基百科 ZIM 文件）的普及，用户需要在无网络环境下访问和查询这些知识。传统的关键字搜索无法满足复杂的问答需求。本项目结合本地大语言模型（Ollama）和检索增强生成（RAG）技术，实现基于本地知识库的智能问答系统。

### 问题陈述

1. **离线知识访问**: 在无网络环境下访问大型知识库
2. **智能问答**: 超越关键字搜索，实现自然语言问答
3. **隐私保护**: 所有数据处理在本地完成，无需上传到云端
4. **资源优化**: 有效利用本地计算资源，支持大规模知识库索引

### 技术动机

- **RAG 技术**: 结合检索和生成的优势，提供准确且有依据的回答
- **本地大模型**: Ollama 提供易用的本地模型部署方案
- **向量检索**: ChromaDB 提供高效的语义搜索能力
- **ZIM 格式**: Kiwix 项目提供的标准离线知识格式

## 应用场景

### 目标用户

1. **研究人员**: 离线查阅学术资料和专业文献
2. **教育工作者**: 在无网络教室中提供知识问答服务
3. **开发者**: 本地技术文档查询和代码知识库
4. **隐私敏感用户**: 不希望数据上传到云端的用户
5. **偏远地区**: 网络条件受限地区的知识获取

### 典型工作流

1. **知识库准备**: 下载并加载 ZIM 文件（如维基百科）
2. **索引构建**: 系统自动建立向量索引
3. **提问查询**: 用户输入自然语言问题
4. **检索增强**: 系统检索相关知识片段
5. **生成回答**: 大模型基于检索内容生成回答
6. **来源追溯**: 显示参考来源便于验证

### 使用案例

- **教育场景**: 学生在离线环境中查询学习资料
- **企业场景**: 内部技术文档和知识库查询
- **研究场景**: 学术论文和参考文献检索
- **个人场景**: 个人知识库管理和问答

## 硬件兼容性

### 最低配置

- **CPU**: 4 核处理器 (Intel i5 或同等 AMD)
- **内存**: 8GB RAM (16GB 推荐)
- **存储**: 10GB 可用空间 (不含 ZIM 文件)
- **GPU**: 非必需，但有 GPU 可加速模型推理

### 推荐配置

- **CPU**: 8 核处理器 (Intel i7/i9 或 AMD Ryzen 7/9)
- **内存**: 32GB RAM (大规模索引需要更多)
- **存储**: 50GB+ SSD (快速索引读取)
- **GPU**: NVIDIA RTX 3060+ (12GB VRAM 以上)

### 性能指标

| 配置 | 索引速度 | 查询延迟 | 并发支持 |
|------|----------|----------|----------|
| 最低配置 | ~100 文档/秒 | 3-5 秒 | 1-2 用户 |
| 推荐配置 | ~500 文档/秒 | 1-2 秒 | 5-10 用户 |
| 高配 (GPU) | ~1000 文档/秒 | <1 秒 | 10+ 用户 |

### 存储需求估算

- **系统本身**: ~500MB
- **索引数据**: 约 ZIM 文件大小的 10-20%
- **模型文件**: 2-8GB (取决于选择的模型)
- **示例**: 10GB 维基百科 ZIM → ~2GB 索引

## 操作系统

### 支持的系统

**Linux**
- Ubuntu 20.04+ (推荐)
- Debian 11+
- Fedora 36+
- Arch Linux (滚动更新)

**macOS**
- macOS 12.0+ (Monterey 及以上)
- 支持 Intel 和 Apple Silicon (M1/M2/M3)
- Apple Silicon 有原生优化

**Windows**
- Windows 10 (64 位)
- Windows 11 (推荐)
- 需要 WSL2 用于某些功能

### 安装说明

**Ubuntu/Debian**
```bash
# 安装系统依赖
sudo apt update
sudo apt install python3-pip python3-venv

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 zim-rag
pip install zim-rag
```

**macOS**
```bash
# 使用 Homebrew 安装 Python
brew install python@3.11

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装 zim-rag
pip install zim-rag
```

**Windows (WSL2)**
```bash
# 在 WSL2 中
sudo apt update
sudo apt install python3-pip python3-venv

python3 -m venv venv
source venv/bin/activate
pip install zim-rag
```

## 依赖环境

### Python 要求

- **版本**: Python 3.10 或更高
- **推荐**: Python 3.11 (最佳性能和兼容性)

### 核心依赖

| 包名 | 版本 | 用途 |
|------|------|------|
| zimfs | >=0.1.0 | ZIM 文件解析 |
| chromadb | >=0.4.0 | 向量数据库 |
| requests | >=2.28.0 | HTTP 客户端 |
| flask | >=2.3.0 | Web 服务 |
| pyside6 | >=6.5.0 | 图形界面 |
| pyqtgraph | >=0.13.0 | 数据可视化 |

### 外部依赖

**Ollama**
- 版本：0.1.0+
- 安装：https://ollama.ai
- 默认端口：11434

**模型推荐**
- llama3 (8B): 平衡性能和准确度
- mistral (7B): 优秀的推理能力
- gemma (7B): Google 开源模型

## 安装过程

### 方法一：pip 安装 (推荐)

```bash
# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装 zim-rag
pip install zim-rag

# 验证安装
zim-rag --version
```

### 方法二：源码安装

```bash
# 克隆仓库
git clone https://github.com/cycleuser/zim-rag.git
cd zim-rag

# 创建虚拟环境并激活
python -m venv venv
source venv/bin/activate

# 安装开发版本
pip install -e .

# 运行测试
pytest tests/
```

### 方法三：Docker 安装

```bash
# 拉取镜像
docker pull zimrag/zim-rag:latest

# 运行容器
docker run -it --rm \
  -v /path/to/zims:/data/zims \
  -v /path/to/index:/data/index \
  -p 5000:5000 \
  zimrag/zim-rag web
```

### 配置说明

**环境变量**
```bash
# Ollama 服务地址
export OLLAMA_HOST=http://localhost:11434

# 索引存储目录
export ZIM_RAG_INDEX=./zim_rag_index

# 日志级别
export ZIM_RAG_LOG=INFO
```

**配置文件** (可选)
```yaml
# config.yaml
ollama:
  host: http://localhost:11434
  model: llama3

index:
  dir: ./zim_rag_index
  chunk_size: 500

ui:
  theme: default
  language: zh-CN
```

## 使用方法

### 命令行界面

**构建索引**
```bash
# 索引单个 ZIM 文件
zim-rag index /path/to/wikipedia.zim

# 索引多个文件
zim-rag index wiki.zim tech.zim medical.zim

# 指定最大文章数
zim-rag index wiki.zim --max-articles 50000
```

**提问查询**
```bash
# 简单提问
zim-rag ask "量子力学的基本原理是什么？"

# 指定模型
zim-rag ask "相对论是什么？" -m mistral

# 指定上下文数量
zim-rag ask "光合作用的过程" -n 10

# 流式输出
zim-rag ask "解释黑洞" --stream

# 保存结果到文件
zim-rag ask "什么是机器学习？" -o answer.txt
```

**交互聊天**
```bash
# 启动聊天模式
zim-rag chat

# 聊天中指定模型
zim-rag chat -m llama3
```

**系统管理**
```bash
# 查看统计信息
zim-rag stats

# 健康检查
zim-rag health

# 生成文档
zim-rag doc "人工智能发展史" --outline 起源 发展 现状 未来
```

### 图形界面

```bash
# 启动 GUI
zim-rag gui

# 禁用嵌入 Web 服务
zim-rag gui --no-web
```

**GUI 功能**
- ZIM 文件管理（添加/移除）
- 索引构建进度显示
- 问答界面（支持 Ctrl+Enter 发送）
- 模型选择和切换
- 来源展示和验证
- 答案导出功能

### Web 界面

```bash
# 启动 Web 服务
zim-rag web

# 指定端口
zim-rag web -p 8080

# 指定监听地址
zim-rag web --host 0.0.0.0 -p 5000
```

**API 端点**
- `GET /` - Web 界面
- `POST /api/ask` - 提问接口
- `POST /api/ask/stream` - 流式提问
- `POST /api/chat` - 聊天接口
- `GET /api/zims` - 列出 ZIM 文件
- `POST /api/zims` - 添加 ZIM 文件
- `POST /api/index/build` - 构建索引
- `GET /api/stats` - 系统统计
- `GET /api/health` - 健康检查

### Python API

```python
from zim_rag import ZIMRAGAPI

# 初始化
api = ZIMRAGAPI(
    zim_paths=["/path/to/wiki.zim"],
    model="llama3",
    ollama_host="http://localhost:11434"
)

# 添加 ZIM 文件
api.add_zim("/path/to/tech.zim")

# 构建索引
result = api.build_index(max_articles=10000)
print(f"索引了 {result.data['total_indexed']} 个文档")

# 提问
result = api.ask("什么是深度学习？")
if result.success:
    print(result.data['answer'])
    print("来源:", result.metadata['sources'])

# 流式提问
for chunk in api.ask_stream("解释量子纠缠"):
    print(chunk, end="", flush=True)

# 聊天
messages = [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
    {"role": "user", "content": "什么是 RAG 技术？"}
]
result = api.chat(messages)

# 生成文档
result = api.generate_document(
    topic="人工智能发展史",
    outline=["起源", "发展历程", "主要流派", "未来趋势"]
)

# 系统管理
stats = api.get_stats()
health = api.check_health()
```

## 运行截图

| GUI 界面 | Web 界面 |
|:--------:|:--------:|
| ![GUI](images/gui.png) | ![Web](images/web.png) |

*注：截图为示意图，实际界面可能因版本不同有所差异*

## 故障排除

### 常见问题

**Ollama 连接失败**
```bash
# 检查 Ollama 是否运行
ollama list

# 重启 Ollama 服务
ollama serve
```

**内存不足**
```bash
# 减少索引文章数
zim-rag index wiki.zim --max-articles 5000

# 减少上下文数量
zim-rag ask "问题" -n 3
```

**索引构建慢**
- 使用 SSD 存储
- 减少 chunk_size
- 升级硬件配置

### 日志调试

```bash
# 启用详细输出
zim-rag -v ask "问题"

# 查看日志文件
tail -f ~/.zim_rag/logs/app.log
```

## 授权协议

本项目采用 **GNU General Public License v3.0 (GPLv3)** 授权。

### 您的权利

- 自由使用：可用于个人或商业用途
- 自由研究：可研究源代码工作原理
- 自由修改：可修改源代码满足需求
- 自由分发：可分发原版或修改版

### 您的义务

- 保留版权和许可声明
- 修改版必须采用相同许可
- 分发时必须提供源代码

详见 [LICENSE](LICENSE) 文件。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

```bash
git clone https://github.com/cycleuser/zim-rag.git
cd zim-rag
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/ -v --cov=zim_rag
```

### 代码规范

```bash
# 格式化代码
black zim_rag/ tests/

# 检查代码
ruff check zim_rag/ tests/
```

## 联系方式

- 项目主页：https://github.com/cycleuser/zim-rag
- 问题反馈：https://github.com/cycleuser/zim-rag/issues

---

## Project Homepage

**GitHub Repository:** https://github.com/cycleuser/zim-rag

**PyPI Package:** https://pypi.org/project/zim-rag/

---

# ZIM-RAG: Local Knowledge Base Q&A System

A Retrieval-Augmented Generation (RAG) system based on ZIM files and local large language models (Ollama).

## Background

With the popularity of offline knowledge bases (such as Wikipedia ZIM files), users need to access and query this knowledge in offline environments. Traditional keyword search cannot meet complex Q&A needs. This project combines local large language models (Ollama) and RAG technology to achieve an intelligent Q&A system based on local knowledge bases.

## Installation

```bash
pip install zim-rag
```

## Quick Start

```bash
# Build index from ZIM files
zim-rag index /path/to/wiki.zim

# Ask a question
zim-rag ask "What is quantum mechanics?"

# Start GUI
zim-rag gui

# Start Web service
zim-rag web --port 5000
```

## Features

- **ZIM File Support**: Parse and index offline ZIM knowledge bases
- **Local LLM**: Powered by Ollama for privacy-preserving inference
- **Semantic Search**: Vector-based retrieval with ChromaDB
- **Multi-interface**: CLI, GUI (PySide6), and Web (Flask)
- **Source Attribution**: All answers include reference sources

## Requirements

- Python 3.10+
- Ollama (https://ollama.ai)
- 8GB+ RAM (16GB recommended)
- 10GB+ storage space

## License

GPL-3.0 License
- 电子邮件：zim-rag@example.com

## 致谢

感谢以下开源项目：

- [Ollama](https://ollama.ai) - 本地大模型部署
- [ChromaDB](https://chromadb.ai) - 向量数据库
- [Kiwix](https://kiwix.org) - ZIM 文件格式
- [PySide6](https://doc.qt.io/qtforpython/) - Python Qt 绑定
