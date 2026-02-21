# Python Docker 项目重构为 NPM 包计划

## 项目概述

将现有的 Python Docker 项目（Qwen TTS API）重构为一个 npm 包，实现完全相同的功能。

## 当前项目分析

### 功能特性
- 调用 Qwen TTS 服务进行语音合成
- 提供 HTTP REST API 接口
- 支持 50+ 种发音人
- 支持多种语言（中文、英文、日语、韩语等）
- SSE 流式处理队列状态

### 核心文件
| 文件 | 功能 |
|------|------|
| `main.py` | 核心 TTS 客户端，包含 `synthesize()` 函数和 API 调用逻辑 |
| `api_server.py` | FastAPI HTTP 服务器，提供 REST API |
| `client_example.py` | 客户端示例代码 |

### API 端点
- `GET /` - API 信息
- `GET /health` - 健康检查
- `GET /voices` - 获取发音人列表
- `GET /languages` - 获取语言列表
- `POST /tts` - 语音合成（JSON）
- `GET /tts` - 语音合成（Query）
- `POST /tts/url` - 语音合成，直接返回音频URL
- `GET /tts/url` - 语音合成，直接返回音频URL（GET方式）
- `GET /audio/{file_id}` - 下载音频

---

## 重构计划

### 1. 项目结构设计

```
qwen-tts/
├── src/
│   ├── index.ts           # 主入口，导出所有模块
│   ├── client.ts          # 核心 TTS 客户端（对应 main.py）
│   ├── server.ts          # HTTP 服务器（对应 api_server.py）
│   ├── types.ts           # TypeScript 类型定义
│   └── constants.ts       # 常量（VOICES, LANGUAGES）
├── dist/                  # 编译输出目录
├── bin/
│   └── cli.js             # CLI 入口脚本
├── package.json
├── tsconfig.json
├── Dockerfile             # Node.js Docker 镜像
├── docker-compose.yml
├── .dockerignore
├── .gitignore
└── README.md
```

### 2. 技术栈选择

| 功能 | Python | Node.js |
|------|--------|---------|
| 运行时 | Python 3.13 | Node.js 20+ |
| 语言 | Python | TypeScript |
| HTTP 服务器 | FastAPI + uvicorn | Express |
| HTTP 客户端 | requests | 原生 fetch |
| SSE 处理 | requests (stream) | 原生 fetch |
| UUID | uuid | crypto.randomUUID() |
| 异步 | asyncio | 原生 Promise/async-await |

### 3. 实现步骤

#### 步骤 1: 初始化 npm 项目
- 创建 `package.json`
- 创建 `tsconfig.json`
- 配置 TypeScript 编译选项

#### 步骤 2: 创建常量和类型定义
- `src/constants.ts` - 定义 VOICES 和 LANGUAGES 常量
- `src/types.ts` - 定义 TypeScript 接口和类型

#### 步骤 3: 实现核心客户端
- `src/client.ts` - 实现 TTS 客户端核心逻辑
  - `getHeaders()` - 获取请求头
  - `predict()` - 初始化预测请求
  - `queueJoin()` - 加入队列请求
  - `queueData()` - 获取队列数据（SSE 流）
  - `downloadAudio()` - 下载音频文件
  - `synthesize()` - 主合成函数

#### 步骤 4: 实现 HTTP 服务器
- `src/server.ts` - 实现 Express 服务器
  - 所有 API 端点
  - 临时文件管理
  - 错误处理

#### 步骤 5: 创建入口文件
- `src/index.ts` - 导出所有模块

#### 步骤 6: 配置 CLI
- `bin/cli.js` - 命令行入口

#### 步骤 7: Docker 支持
- 更新 `Dockerfile` 为 Node.js 版本
- 更新 `docker-compose.yml`

#### 步骤 8: 清理旧文件
- 删除 Python 相关文件（main.py, api_server.py, client_example.py, pyproject.toml, uv.lock, .python-version）

### 4. package.json 配置

```json
{
  "name": "qwen-tts",
  "version": "0.1.0",
  "description": "通义千问语音合成 API 客户端和服务器",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "bin": {
    "qwen-tts": "./bin/cli.js",
    "qwen-tts-server": "./bin/cli.js"
  },
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js",
    "dev": "ts-node src/server.ts"
  },
  "dependencies": {
    "express": "^4.18.2"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^20.10.0",
    "typescript": "^5.3.0",
    "ts-node": "^10.9.2"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### 5. API 兼容性

确保 Node.js 版本的 API 与 Python 版本完全兼容：
- 相同的端点路径
- 相同的请求/响应格式
- 相同的错误处理

### 6. 文件删除清单

重构完成后删除以下 Python 相关文件：
- `main.py`
- `api_server.py`
- `client_example.py`
- `pyproject.toml`
- `uv.lock`
- `.python-version`

---

## 预期结果

重构后的 npm 包将提供：
1. **编程 API** - 可作为库在其他 Node.js 项目中使用
2. **CLI 工具** - 命令行直接调用
3. **HTTP 服务器** - Docker 部署 REST API 服务

所有功能与原 Python 版本完全一致。
