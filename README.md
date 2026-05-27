# E-Commerce Operations Platform

> 多平台电商数据同步、智能分析报表与自动化运营管理平台

一站式电商运营管理后台，聚合 **淘宝 / Shopify / WooCommerce / Shopee / Lazada** 多平台店铺数据，提供销售分析、库存管理、智能选品、自动化规则、客服自动回复、运营复盘等核心功能。基于 FastAPI + SQLAlchemy 异步架构，从数据采集到运营决策形成完整闭环。

## 功能总览

| 模块 | 功能 |
|------|------|
| **用户系统** | 注册 / 登录 / JWT 认证 / 密码强度校验 / 操作审计日志 |
| **数据看板** | 核心指标（销售额、订单数、客单价）实时展示 / 销售趋势曲线 / 品类分布饼图 / Top10 畅销排行 / 库存预警 |
| **销售分析** | 多维度趋势分析（7/30/90 天）/ 日度明细 / 环比增长 / 品类聚合 |
| **库存管理** | 库存分类（正常/偏低/缺货）/ 品类分布 / 库存预警列表 |
| **店铺管理** | 多平台接入（淘宝/Shopify/WooCommerce/Shopee/Lazada）/ 数据同步触发 |
| **自动化规则** | 条件触发自动化（库存预警/销售暴涨提醒）/ 启用/停用切换 |
| **智能选品** | 基于数据的选品推荐 / 综合评分 0-100 / 审核流程（待审/通过/拒绝） |
| **自动化客服** | 关键词匹配自动回复（包含/精确/正则）/ 测试匹配 / 使用统计 |
| **运营建议** | 自动生成优化建议（补货/调价/营销/库存）/ 采纳/忽略操作 |
| **复盘分析** | 周度/月度经营复盘 / 自动洞察分析 + 行动项 / 草稿/发布/归档 |
| **第三方密钥** | AI 服务商密钥管理（OpenAI/Claude/DeepSeek 等）/ AES 加密存储 / 启用/停用 |
| **国际化** | 中英文双语界面 / Cookie + Accept-Language 自动检测 |
| **操作日志** | 完整审计追踪 / 按操作类型 + 资源类型筛选 / 分页浏览 |
| **安全防护** | JWT 认证 / 令牌桶限流（登录 5次/分 + API 60次/分）/ HSTS / X-Frame-Options / CORS 白名单 / 请求体限制 / 加密密钥可轮换 |

## 技术栈

| 层 | 技术 |
| --- | --- |
| **后端** | Python 3.14, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **数据库** | PostgreSQL 16, Redis 7 |
| **前端** | Jinja2 模板, 自定义 CSS 设计系统, Chart.js, 零 JS 框架依赖 |
| **认证** | JWT (python-jose), bcrypt 密码哈希 |
| **加密** | Fernet (AES-128-CBC + HMAC-SHA256), PBKDF2 密钥派生 |
| **异步任务** | Celery + Redis (数据同步/报表生成) |
| **部署** | Docker Compose, Nginx (反向代理 + 限流) |
| **测试** | pytest, httpx (ASGI 异步), 124 个测试用例 |

## 架构亮点

- **平台适配器模式**: 统一接口 (`PlatformAdapter`) 屏蔽各平台 API 差异，新增平台只需实现 5 个方法 + 注册工厂
- **双层缓存**: L1 内存 (30s TTL / LRU) + L2 Redis，`@cached` 装饰器自动管理
- **数据隔离**: 用户 → 店铺 → 实体，三层权限隔离，测试覆盖隔离场景
- **加密可轮换**: 加密密钥支持 `reencrypt_api_key()`，迁移不丢数据
- **零 Bootstrap**: 全自定义 CSS 设计系统 + 纯原生 JavaScript
- ****i18n 架构**: 翻译 JSON + `_(text)` 全局函数，Cookie/Header 自动语言检测

## 快速开始

### 前置要求

- Docker & Docker Compose（推荐）
- 或 Python 3.14+ & PostgreSQL 16 & Redis 7

### Docker 一键部署

```bash
# 1. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，修改 SECRET_KEY 和 ENCRYPTION_KEY（开发环境可用默认值）

# 2. 启动全部服务（从项目根目录执行）
docker compose -f docker/docker-compose.yml up -d

# 3. 访问
open http://localhost:8000
```

> 首次启动自动建表、填充演示数据。等待 10-15 秒后即可访问。
> 如果端口 80 被占用，可使用 http://localhost:8000。

### 手动启动

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env

# 3. 初始化数据库
alembic upgrade head

# 4. 启动开发服务器
uvicorn app.main:app --reload

# 5. 填充演示数据（可选）
python -m app.seed_data
```

### 演示账号

首次启动种子数据自动创建演示账号:

```
邮箱:    demo@example.com
密码:    Demo1234!
```

登录后即可查看：数据看板、店铺管理、销售分析、选品推荐、运营建议等完整功能。

## 运行测试

```bash
cd backend
python -m pytest tests/ -v --tb=short
```

124 个测试覆盖：认证、店铺、订单、选品、自动化、客服、建议、复盘、日志、三方密钥、分析、Dashboard、适配器、核心工具函数。

## 项目结构

```
backend/
├── app/
│   ├── api/v1/             # API 路由（auth / stores / analytics / 自动化 / 等）
│   │   ├── pages.py        # 页面路由（Jinja2 模板渲染）
│   │   └── *.py            # REST 端点
│   ├── core/               # 核心业务逻辑
│   │   ├── adapters/       # 平台适配器（shopify / woocommerce / taobao / shopee / lazada）
│   │   ├── analytics/      # 销售分析 / 库存分析 / 趋势分析
│   │   ├── auto_reply/     # 自动回复服务
│   │   ├── automation/     # 自动化规则引擎
│   │   ├── product_selection/ # 智能选品
│   │   ├── retrospective/  # 复盘分析
│   │   ├── suggestion/     # 运营建议
│   │   ├── sync/           # 数据同步（订单/商品/客户）
│   │   ├── auth.py         # JWT + 密码
│   │   ├── crypto.py       # Fernet 加密
│   │   ├── i18n.py         # 国际化
│   │   └── operation_log.py # 审计日志
│   ├── infrastructure/     # 基础设施（数据库/缓存/限流/Celery）
│   ├── models/             # SQLAlchemy ORM 模型（14 个模型）
│   ├── static/             # 静态资源（CSS, JS）
│   ├── templates/          # Jinja2 模板（12 个页面）
│   └── config.py           # Pydantic 配置
├── tests/                  # 124 个测试用例
│   ├── test_api/           # API 集成测试（含数据隔离）
│   ├── test_adapters/      # 平台适配器测试
│   ├── test_analytics/     # 分析引擎测试
│   └── test_core/          # 核心工具测试
└── migrations/             # Alembic 数据库迁移
docker/
├── Dockerfile              # Python 3.12-slim, 非 root 运行
├── docker-compose.yml      # Nginx + API + Celery + Postgres + Redis
└── nginx.conf              # 安全加固 + 限流
```

## 环境变量

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `SECRET_KEY` | JWT 签名密钥 | **必填** |
| `ENCRYPTION_KEY` | Fernet 加密密钥 | **必填** |
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql+asyncpg://postgres:...` |
| `CELERY_BROKER_URL` | Redis 消息队列 | `redis://redis:6379/0` |
| `DEBUG` | 调试模式 | `false` |
| `RATE_LIMIT_ENABLED` | 限流开关 | `true` |
| `CORS_ORIGINS` | 跨域白名单 | `http://localhost:8000,...` |

## 支持的电商平台接入

| 平台 | 凭证说明 | 文档 |
|------|----------|------|
| **淘宝** | App Key + App Secret | 开放平台控制台 |
| **Shopify** | API Key + Access Token | Shopify Partners |
| **WooCommerce** | Consumer Key + Consumer Secret | WooCommerce → 设置 → API |
| **Shopee** | Partner ID + Secret Key + Shop ID | Shopee Partner 控制台 |
| **Lazada** | App Key + App Secret + Region | Lazada Open Platform |
