# Knowledge Base Service (KB Service)

基于 RAG (Retrieval-Augmented Generation) 的知识库问答服务，使用本地 Ollama 模型。

## 架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  GitHub     │────▶│  Document   │────▶│  Embedding  │
│  Repo       │     │  Processor  │     │  (Ollama)   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                       ┌────────▼────────┐
                                       │   Vector DB     │
                                       │   (ChromaDB)    │
                                       └────────┬────────┘
                                                │
┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
│   User      │────▶│   Query     │────▶│   Search    │
│   Query     │     │   Embed     │     │   (Top-K)   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                       ┌────────▼────────┐
                                       │  Context + LLM  │
                                       │   (Ollama)      │
                                       └────────┬────────┘
                                                │
                                       ┌────────▼────────┐
                                       │    Answer       │
                                       └─────────────────┘
```

## 特性

- 🔍 **智能检索** - 基于向量相似度的知识检索
- 🤖 **本地 LLM** - 使用 Ollama 本地模型，无需联网
- 📝 **自动同步** - 自动从 GitHub 同步知识库更新
- 🚀 **高性能** - FastAPI 异步处理
- 🔧 **易扩展** - 模块化设计

## 快速开始

### 1. 安装 Ollama 并拉取模型

```bash
# 安装 Ollama (如果还没安装)
curl -fsSL https://ollama.com/install.sh | sh

# 启动 Ollama 服务
ollama serve

# 拉取所需模型
ollama pull nomic-embed-text
ollama pull qwen2.5
```

### 2. 配置 KB Service

```bash
# 克隆仓库
git clone https://github.com/tangjie133/kb-service.git
cd kb-service

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置你的 GitHub 仓库
```

### 3. 启动服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
./scripts/start.sh
```

服务将在 http://localhost:8000 启动

### 4. 测试 API

```bash
# 查询知识库
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "传感器读不到心率怎么办",
    "top_k": 3,
    "generate_answer": true
  }'
```

## API 接口

### POST /query

查询知识库并生成回答

**请求体:**
```json
{
  "query": "用户问题",
  "top_k": 5,
  "generate_answer": true
}
```

**响应:**
```json
{
  "query": "用户问题",
  "results": [
    {
      "id": "chunk_0",
      "content": "相关内容",
      "source_file": "hardware/sensor.md",
      "similarity": 0.92,
      "metadata": {}
    }
  ],
  "answer": "生成的回答",
  "stats": {
    "total_documents": 100,
    "results_found": 5
  }
}
```

### POST /sync

手动触发知识库同步

### GET /health

健康检查

### GET /stats

服务统计信息

## 知识库格式

知识库使用 Markdown 文件，支持 YAML frontmatter:

```markdown
---
title: 文档标题
category: troubleshooting
tags: [sensor, hardware]
---

# 文档标题

## 问题
描述问题...

## 解决方案
解决步骤...
```

## 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| GITHUB_REPO | 知识库 GitHub 仓库 | - |
| GITHUB_TOKEN | GitHub Token (可选) | - |
| OLLAMA_HOST | Ollama 服务地址 | http://localhost:11434 |
| EMBEDDING_MODEL | 嵌入模型 | nomic-embed-text |
| LLM_MODEL | LLM 模型 | qwen2.5 |
| CHUNK_SIZE | 文档分块大小 | 500 |
| TOP_K | 检索结果数量 | 5 |

## Docker 部署

```bash
# 构建镜像
docker build -t kb-service .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -e GITHUB_REPO=your/repo \
  -v $(pwd)/data:/app/data \
  --network host \
  kb-service
```

## 客户端使用

```python
from kb_client import KBClient

kb = KBClient("http://localhost:8000")

# 查询
result = kb.query_sync("传感器问题")
print(result["answer"])
```

## 许可证

MIT
