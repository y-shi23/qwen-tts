# 使用官方 Python 镜像作为基础
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 创建虚拟环境
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# 复制项目文件
COPY pyproject.toml ./

# 安装依赖（不安装包本身，只安装依赖）
RUN uv pip install --no-cache fastapi[standard]>=0.128.0 requests>=2.31.0

# 复制应用代码
COPY main.py api_server.py client_example.py ./

# 创建临时目录
RUN mkdir -p /tmp/qwen_tts

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
