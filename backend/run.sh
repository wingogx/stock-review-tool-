#!/bin/bash

# 激活虚拟环境并启动 FastAPI 服务器

cd "$(dirname "$0")"

echo "============================================"
echo "🚀 启动 FastAPI 后端服务"
echo "============================================"

# 激活虚拟环境
source venv/bin/activate

# 设置 PYTHONPATH
export PYTHONPATH=$(pwd)

# 启动服务器
echo "📡 启动开发服务器: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "============================================"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
