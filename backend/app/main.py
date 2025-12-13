"""
股票短线复盘工具 - FastAPI 后端主程序
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量（从项目根目录）
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 应用元数据
APP_TITLE = "股票短线复盘 API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
股票短线复盘工具后端 API

## 功能模块

* **市场指数** - 获取大盘指数数据
* **市场情绪** - 市场情绪分析指标
* **涨停池** - 涨停/跌停个股详细信息
* **龙虎榜** - 龙虎榜数据和席位分析
* **热门概念** - 热门概念板块追踪
* **自选股** - 自选股监控和异动提醒

## 数据源

* Tushare Pro（6000+积分）- 龙虎榜、个股行情
* AKShare（免费）- 涨停池、概念板块
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时执行初始化，关闭时执行清理
    """
    # 启动时
    print("=" * 60)
    print(f"🚀 {APP_TITLE} v{APP_VERSION} 启动中...")
    print("=" * 60)
    print(f"📡 Supabase URL: {os.getenv('SUPABASE_URL', 'Not configured')}")
    print(f"🔑 Tushare Token: {'已配置' if os.getenv('TUSHARE_TOKEN') else '未配置'}")
    print(f"🌍 环境: {os.getenv('ENV', 'development')}")
    print("=" * 60)

    yield

    # 关闭时
    print("=" * 60)
    print(f"👋 {APP_TITLE} 关闭")
    print("=" * 60)


# 创建 FastAPI 应用实例
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc
    openapi_url="/openapi.json" # OpenAPI schema
)

# 配置 CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js 开发服务器
        "http://localhost:8000",  # 本地后端
        # 生产环境域名稍后添加
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 基础路由
# ============================================

@app.get("/", tags=["基础"])
async def root():
    """根路径 - 返回 API 基本信息"""
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "status": "运行中",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["基础"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": APP_TITLE,
        "version": APP_VERSION,
        "environment": os.getenv("ENV", "development")
    }


@app.get("/config", tags=["基础"])
async def get_config():
    """获取配置信息（不包含敏感数据）"""
    return {
        "supabase_configured": bool(os.getenv("SUPABASE_URL")) and
                              os.getenv("SUPABASE_URL") != "your_supabase_url",
        "tushare_configured": bool(os.getenv("TUSHARE_TOKEN")),
        "environment": os.getenv("ENV", "development"),
        "port": os.getenv("PORT", "8000")
    }


# ============================================
# 路由注册
# ============================================

from app.routers import market_router, limit_stocks_router, concepts_router, sector_router, sentiment_router, stock_router, backtest_router

# 市场数据路由
app.include_router(
    market_router,
    prefix="/api/market",
    tags=["市场数据"]
)

# 涨停池路由
app.include_router(
    limit_stocks_router,
    prefix="/api/limit",
    tags=["涨停池"]
)

# 概念板块路由
app.include_router(
    concepts_router,
    prefix="/api/concepts",
    tags=["概念板块"]
)

# 板块分析路由
app.include_router(
    sector_router,
    tags=["板块分析"]
)

# 情绪分析路由
app.include_router(
    sentiment_router,
    tags=["情绪分析"]
)

# 个股分析路由
app.include_router(
    stock_router,
    prefix="/api/stock",
    tags=["个股分析"]
)

# 回测分析路由
app.include_router(
    backtest_router,
    prefix="/api/backtest",
    tags=["回测分析"]
)

# TODO: 龙虎榜路由（需要先实现数据采集）
# app.include_router(dragon_tiger_router, prefix="/api/dragon-tiger", tags=["龙虎榜"])


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # 开发模式自动重载
        log_level="info"
    )
