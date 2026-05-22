# ============================================================
# Chimera Dockerfile
# AI 跨游戏角色与资产融合迁移引擎
# ============================================================

FROM python:3.10-slim

LABEL org.chimera.name="Chimera"
LABEL org.chimera.description="AI Cross-Game Character Migration Engine"
LABEL org.chimera.version="0.1.0"

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 工作目录
WORKDIR /app/chimera

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 项目文件
COPY . .

# 数据目录
RUN mkdir -p knowledge logs output

# 环境变量
ENV PYTHONPATH=/app/chimera
ENV CHIMERA_API_HOST=0.0.0.0
ENV CHIMERA_API_PORT=8004

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# 暴露端口
EXPOSE 8004

# 启动命令
CMD ["python3", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8004"]
