# RAG 多用户智能客服系统

## 📖 项目简介

本项目是一个基于 **RAG (Retrieval-Augmented Generation)** 架构的多用户智能客服系统。它结合了向量数据库检索与大语言模型（LLM），能够根据用户上传的本地知识库（TXT文档）进行精准问答。

**核心亮点：**
- ✅ **多用户隔离**：支持用户注册/登录，不同用户的对话历史完全隔离。
- ✅ **持久化存储**：
  - **对话历史**：使用 **Redis** 存储，设置 7 天自动过期，节省内存。
  - **用户信息**：永久存储在 Redis 中。
  - **知识库向量**：使用 **ChromaDB** 本地持久化存储。
- ✅ **流式响应**：支持打字机效果的实时回答体验。
- ✅ **Web 界面**：基于 Streamlit 构建的交互式前端，包含知识库上传与聊天界面。


## 📂 项目目录结构

```text
RAG项目案例（可多用户登录）/
├── app_multi_user.py       # [主入口] 多用户聊天 Web 界面 (Streamlit)
├── app_file_uploader.py    # [辅助入口] 知识库文件上传与管理界面
├── rag.py                  # [核心逻辑] RAG 链式调用封装 (RagService)
├── knowledge_base.py       # [知识库] 文档切片、向量化及存入 ChromaDB 的逻辑
├── vector_stores.py        # [向量服务] ChromaDB 连接与检索器封装
├── redis_history_store.py  # [历史记录] 基于 Redis 的聊天历史存储实现 (ManualRedisChatHistory)
├── user_service.py         # [用户服务] 用户注册、登录及密码哈希处理
├── config_data.py          # [配置文件] 模型名称、路径、分割参数等全局配置
├── .env                    # [环境变量] API Key 等敏感信息 (需自行创建)
├── requirements.txt        # [依赖列表] Python 第三方库
├── chroma_db/              # [数据存储] ChromaDB 向量数据库本地存储目录 (自动生成)
├── data/                   # [示例数据] 存放待上传的 TXT 知识库文件
└── README.md               # 项目说明文档
```

---

## 🛠️ 技术栈与依赖

### 核心框架
- **LangChain**: 编排 LLM 应用流程。
- **Streamlit**: 快速构建 Web 交互界面。
- **Redis**: 后端数据存储与会话管理。

### 数据存储
1. **ChromaDB**: 用于存储知识库文本的向量索引，支持本地持久化 (`./chroma_db`)。
2. **Redis**: 
   - 存储用户账号信息（永久）。
   - 存储用户对话历史（TTL 7天）。

### 模型支持
- **Embedding**: `text-embedding-3-small` (OpenAI) 或兼容模型。
- **Chat Model**: `gpt-3.5-turbo` (OpenAI) 或兼容模型。

---

## 🚀 快速开始

### 1. 环境准备

确保已安装 **Python 3.8+** 和 **Redis Server**。

#### 启动 Redis
```bash
# Windows (如果安装了 Redis)
redis-server

# Docker (推荐)
docker run -d --name redis-stack -p 6379:6379 redis/redis-stack:latest
```

### 2. 安装依赖

建议使用虚拟环境：

```bash
python -m venv venv
# Windows 激活
venv\Scripts\activate
# macOS/Linux 激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置 API Key

在项目根目录创建 `.env` 文件，填入你的 LLM API 配置：

```env
OPENAI_API_KEY_FREE0=sk-your-api-key-here
OPENAI_BASE_URL0=https://api.your-proxy.com/v1
```

### 4. 运行项目

#### 方式 A：启动多用户聊天主程序 (推荐)
```bash
streamlit run app_multi_user.py
```
*访问浏览器显示的地址（通常为 http://localhost:8501），先注册账号，然后上传知识库或直接聊天。*

#### 方式 B：启动知识库上传专用界面
```bash
streamlit run app_file_uploader.py
```

---

## 💡 功能使用说明

1. **注册/登录**：
   - 在左侧侧边栏切换“登录”或“注册”标签。
   - 注册后，使用用户名和密码登录。
   - *注意：刷新页面后，登录状态会通过本地存储自动保持。*

2. **上传知识库**：
   - 登录成功后，在主界面或运行 `app_file_uploader.py`。
   - 上传 `.txt`格式的文件。系统会自动去重（MD5校验）、切片并向量化存入 ChromaDB。

3. **智能问答**：
   - 在聊天框输入问题。
   - 系统会从 ChromaDB 检索相关文档片段，结合聊天记录，由 LLM 生成回答。
   - 回答支持流式输出，体验更流畅。

4. **历史记录**：
   - 每次对话会自动保存到 Redis。
   - 即使关闭浏览器，下次登录同一账号仍能看到最近 7 天的对话历史。

---

## ⚙️ 配置说明 (config_data.py)

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| collection_name ChromaDB 集合名称 | `"rag"` |
| persist_directory ChromaDB 本地存储路径 | `"./chroma_db"` |
| chunk_size | 文本切片大小 | `1000` |
| chunk_overlap | 切片重叠字符数 | `100` |
| embedding_model_name | 嵌入模型名称 | `"text-embedding-3-small"` |
| chat_model_name | 聊天模型名称 | `"gpt-3.5-turbo"` |
| similarity_threshold | 检索返回文档数量 (k) | `1` |

---

## ❓ 常见问题

1. **Redis 连接失败？**
   - 请确保 Redis 服务正在运行，且端口为 `6379`。
   - 检查 `redis_history_store.py`中的连接地址。

2. **聊天没有上下文？**
   - 检查 [rag.py] 中的 `RunnableWithMessageHistory` 配置是否正确。
   - 确保 Redis 中确实写入了数据（使用 `redis-cli LRANGE chat_history:用户名 0 -1` 查看）。

3. **上传文件提示“已存在”？**
   - 系统使用了 MD5 去重机制。如果文件内容未变，不会重复向量化。如需重新导入，请删除`md5.text` 文件或修改文件内容。


### 2. requirements.txt 文件内容

请复制以下内容，保存为项目根目录下的 [requirements.txt] 文件：

```text
# Web Framework
streamlit>=1.31.0

# LangChain & AI Core
langchain>=0.1.0
langchain-core>=0.1.0
langchain-community>=0.0.10
langchain-openai>=0.0.5
langchain-chroma>=0.1.0

# Vector Database
chromadb>=0.4.22

# Redis & Data Storage
redis>=5.0.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.5.0
tiktoken>=0.5.0
```