# E-Commerce Operations Platform

多平台电商自动化运营平台 — 数据分析与报表引擎，支持 Shopify、WooCommerce 等平台。

## 核心功能

| 模块 | 功能 | 状态 |
|------|------|------|
| **Dashboard** | 销售总览、订单统计、商品概览 | ✅ MVP |
| **销售分析** | GMV、订单量、客单价、按日/周/月聚合 | ✅ MVP |
| **库存分析** | 库存周转、缺货预警、超储商品、品类分布 | ✅ MVP |
| **趋势分析** | 环比/同比增长、趋势图表 | ✅ MVP |
| **Top 商品** | 畅销商品排名 | ✅ MVP |
| **报表导出** | CSV 格式销售/库存报表 | ✅ MVP |
| **自动化规则** | 条件触发的自动化引擎 | ✅ 框架 |
| **Shopify 适配器** | 对接 Shopify REST API | ✅ 可用 |
| **WooCommerce 适配器** | 对接 WooCommerce API | 📋 计划中 |

## 快速开始

### 使用 Docker（推荐）

```bash
# 克隆并启动
cd docker
cp ../backend/.env.example .env
docker-compose up -d

# 运行数据库迁移
docker-compose exec api alembic upgrade head

# 访问
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 本地开发

```bash
# 1. 创建虚拟环境
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env

# 4. 启动服务
uvicorn app.main:app --reload
```

## 项目结构

```
backend/
├── app/
│   ├── api/v1/          # REST API 路由
│   ├── core/
│   │   ├── adapters/    # 平台适配器（适配器模式）
│   │   ├── analytics/   # 分析引擎
│   │   ├── automation/  # 自动化规则引擎
│   │   └── sync/        # 数据同步管道
│   ├── infrastructure/  # 数据库、缓存、Celery
│   └── models/          # SQLAlchemy 数据模型
├── tasks/               # Celery 异步任务
├── migrations/          # Alembic 数据库迁移
└── tests/               # 测试
```

## 平台适配器

支持多电商平台，通过适配器模式统一接口：

- **Shopify** — REST API v2024-07 (✅ 已实现)
- **WooCommerce** — REST API v3 (📋 计划中)
- **自定义** — 实现 `PlatformAdapter` 接口即可接入

详见 [适配器开发指南](docs/adapters.md)。

## API 文档

服务启动后访问 `http://localhost:8000/docs` 查看 Swagger 文档。
或查看 [API 参考](docs/api.md)。

## 许可证

MIT
