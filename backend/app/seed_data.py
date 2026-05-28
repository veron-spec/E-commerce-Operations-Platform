"""生成模拟数据，让看板和 API 有数据可展示。

用法：
    docker-compose exec api python -m app.seed_data
"""
import asyncio
import random
from datetime import datetime, timedelta, timezone

from app.infrastructure.database import async_session
from app.models.store import Store
from app.models.product import Product
from app.models.order import Order
from app.models.customer import Customer


def _utcnow() -> datetime:
    """Return naive UTC datetime (columns are TIMESTAMP WITHOUT TIME ZONE)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# 模拟数据
DEMO_PRODUCTS = [
    {"title": "无线蓝牙耳机 Pro", "category": "电子产品", "price": 299, "sku": "BL-001", "stock": 85},
    {"title": "智能手表 S3", "category": "电子产品", "price": 899, "sku": "SW-003", "stock": 42},
    {"title": "便携充电宝 20000mAh", "category": "电子产品", "price": 159, "sku": "PB-002", "stock": 120},
    {"title": "运动跑鞋 透气款", "category": "运动户外", "price": 459, "sku": "SN-001", "stock": 3},
    {"title": "瑜伽垫加厚防滑", "category": "运动户外", "price": 89, "sku": "YG-001", "stock": 67},
    {"title": "保温杯 500ml 不锈钢", "category": "家居生活", "price": 69, "sku": "CU-001", "stock": 200},
    {"title": "护眼台灯 LED", "category": "家居生活", "price": 129, "sku": "LA-001", "stock": 0},
    {"title": "纯棉T恤 简约白", "category": "服装鞋帽", "price": 79, "sku": "TS-001", "stock": 8},
    {"title": "牛仔夹克 经典款", "category": "服装鞋帽", "price": 259, "sku": "JK-001", "stock": 35},
    {"title": "有机绿茶 250g", "category": "食品饮料", "price": 49, "sku": "TE-001", "stock": 150},
    {"title": "坚果礼盒 混合装", "category": "食品饮料", "price": 128, "sku": "NU-001", "stock": 6},
    {"title": "机械键盘 青轴", "category": "电子产品", "price": 399, "sku": "KB-001", "stock": 22},
    {"title": "鼠标垫 大号 电竞", "category": "电子产品", "price": 39, "sku": "MP-001", "stock": 300},
    {"title": "双肩背包 防水", "category": "运动户外", "price": 199, "sku": "BP-001", "stock": 0},
    {"title": "护肤礼盒 保湿套装", "category": "个护美妆", "price": 329, "sku": "SK-001", "stock": 18},
]


async def seed():
    async with async_session() as db:
        # 检查是否已有数据
        from sqlalchemy import select, func
        count = await db.execute(select(func.count(Store.id)))
        if count.scalar() > 0:
            print("数据库已有数据，跳过模拟数据生成")
            return

        # 1. 创建演示用户
        from app.models.user import User
        from app.core.auth import hash_password
        user = User(
            email="demo@example.com",
            name="演示用户",
            password_hash=hash_password("Demo1234!"),
        )
        db.add(user)
        await db.flush()
        print(f"   - 演示用户：demo@example.com / Demo1234!")

        # 2. 创建模拟店铺（关联到演示用户）
        store = Store(
            user_id=user.id,
            name="我的淘宝店",
            platform_type="taobao",
            store_url="demo_taobao_shop",
            api_key="demo_key",
            api_secret="demo_secret",
            is_active=True,
        )
        db.add(store)
        await db.flush()

        # Shopee 演示店铺
        shopee = Store(
            user_id=user.id,
            name="跨境 Shopee 店",
            platform_type="shopee",
            store_url="123456789",  # Shop ID
            api_key="demo_partner_id",
            api_secret="demo_secret_key",
            is_active=True,
        )
        db.add(shopee)
        await db.flush()

        # Lazada 演示店铺
        lazada = Store(
            user_id=user.id,
            name="Lazada 东南亚店",
            platform_type="lazada",
            store_url="thailand",  # Region
            api_key="demo_app_key",
            api_secret="demo_app_secret",
            is_active=True,
        )
        db.add(lazada)
        await db.flush()

        # 2. 创建商品
        products = []
        for i, p in enumerate(DEMO_PRODUCTS):
            product = Product(
                store_id=store.id,
                platform_id=f"100{i+1:03d}",
                title=p["title"],
                price=p["price"],
                sku=p["sku"],
                category=p["category"],
                status="active",
                inventory_quantity=p["stock"],
                created_at=_utcnow() - timedelta(days=random.randint(30, 90)),
            )
            db.add(product)
            products.append(product)
        await db.flush()

        # 3. 创建过去 30 天的订单
        now = _utcnow()
        order_id = 10000
        for day_offset in range(30, 0, -1):
            date = now - timedelta(days=day_offset)
            # 每天 3-15 单，周末更多
            is_weekend = date.weekday() >= 5
            daily_orders = random.randint(3, 8) if not is_weekend else random.randint(5, 15)

            for _ in range(daily_orders):
                order_id += 1
                # 随机选 1-3 个商品
                num_items = random.randint(1, 3)
                chosen = random.sample(products, num_items)

                items = []
                total = 0
                for cp in chosen:
                    qty = random.randint(1, 3)
                    item_total = cp.price * qty
                    total += item_total
                    items.append({
                        "product_id": cp.platform_id,
                        "title": cp.title,
                        "sku": cp.sku,
                        "quantity": qty,
                        "price": str(cp.price),
                    })

                # 随机折扣
                discount = round(total * random.uniform(0, 0.05), 2)
                hour = random.randint(8, 23)
                minute = random.randint(0, 59)

                order = Order(
                    store_id=store.id,
                    platform_id=str(order_id),
                    order_number=str(order_id),
                    email=f"buyer{order_id}@example.com",
                    line_items=items,
                    total_price=total - discount,
                    subtotal_price=total,
                    total_discount=discount,
                    financial_status=random.choice(["paid", "paid", "paid", "refunded"]),
                    fulfillment_status=random.choice(["fulfilled", "fulfilled", "unfulfilled"]),
                    created_at=date.replace(hour=hour, minute=minute),
                )
                db.add(order)

        # 4. 创建自动回复规则
        from app.models.auto_reply import AutoReply
        auto_replies = [
            AutoReply(store_id=store.id, name="发货咨询", trigger_keywords=["发货", "物流", "快递", "什么时候到"], match_type="contains",
                      reply_template="亲，您的订单已发货！快递单号 {{order.tracking_number}}，预计 {{estimate_delivery}} 到达。",
                      priority=1, is_enabled=True, usage_count=47),
            AutoReply(store_id=store.id, name="退换货咨询", trigger_keywords=["退货", "退款", "换货", "退钱"], match_type="contains",
                      reply_template="亲，关于退换货问题，请您提供订单号，我们将尽快为您处理。7天无理由退货，15天质量问题换货。",
                      priority=2, is_enabled=True, usage_count=23),
            AutoReply(store_id=store.id, name="欢迎语", trigger_keywords=["你好", "您好", "在吗", "有人吗"], match_type="contains",
                      reply_template="您好！欢迎光临！我是智能客服助手，请问有什么可以帮助您的？",
                      priority=0, is_enabled=True, usage_count=156),
        ]
        for ar in auto_replies:
            db.add(ar)
        await db.flush()

        # 5. 创建自动化规则
        from app.models.automation_rule import AutomationRule
        rules = [
            AutomationRule(store_id=store.id, name="库存预警 - 自动通知", trigger_type="scheduled",
                           conditions={"field": "inventory_quantity", "operator": "lt", "value": 10},
                           actions=[{"type": "notify", "channel": "email",
                                     "message": "商品 {{product.title}} 库存不足，当前库存: {{product.inventory_quantity}}"}],
                           is_enabled=True, last_run_at=_utcnow() - timedelta(hours=2)),
            AutomationRule(store_id=store.id, name="销售暴涨提醒", trigger_type="event",
                           conditions={"field": "daily_revenue", "operator": "gte", "value": 5000},
                           actions=[{"type": "notify", "channel": "app", "message": "今日销售额已超过 ¥5,000！"}],
                           is_enabled=True, last_run_at=_utcnow() - timedelta(hours=6)),
        ]
        for rule in rules:
            db.add(rule)
        await db.flush()

        # 6. 创建选品数据
        from app.models.product_selection import ProductSelection
        selections = [
            ProductSelection(store_id=store.id, product_id=products[0].id, title="无线蓝牙耳机 Pro", platform="taobao", source="analytics",
                             category="电子产品", price=299, sales_volume=1560, growth_rate=32.5, margin=45.0, selection_score=92,
                             reason="近30天销量增长32%，毛利率45%，市场竞争度低", status="approved"),
            ProductSelection(store_id=store.id, product_id=products[2].id, title="便携充电宝 20000mAh", platform="taobao", source="analytics",
                             category="电子产品", price=159, sales_volume=2840, growth_rate=18.2, margin=38.0, selection_score=85,
                             reason="夏季出行高峰，大容量充电宝需求旺盛", status="approved"),
            ProductSelection(store_id=store.id, product_id=products[1].id, title="智能手表 S3", platform="shopify", source="manual",
                             category="电子产品", price=899, sales_volume=420, growth_rate=55.0, margin=52.0, selection_score=78,
                             reason="新品类拓展机会，价格空间大，品牌溢价能力高"),
            ProductSelection(store_id=store.id, title="夏季冰丝凉席", platform="taobao", source="manual",
                             category="家居生活", price=89, sales_volume=3200, growth_rate=120.0, margin=55.0, selection_score=95,
                             reason="季节性爆品，搜索热度上涨300%", status="approved"),
            ProductSelection(store_id=store.id, title="桌面收纳盒 3格", platform="taobao", source="analytics",
                             category="家居生活", price=29, sales_volume=8900, growth_rate=8.5, margin=42.0, selection_score=65,
                             reason="销量高但利润有限，作为引流款", status="archived"),
        ]
        for sel in selections:
            db.add(sel)
        await db.flush()

        # 7. 创建运营建议
        from app.models.suggestion import Suggestion
        suggestions = [
            Suggestion(store_id=store.id, suggestion_type="restock",
                       title="库存不足提醒：运动跑鞋仅剩 3 件", priority="high",
                       description="运动跑鞋透气款（SKU: SN-001）当前库存仅剩3件，低于安全库存线。建议立即补货，避免缺货。",
                       data_source="inventory_analyzer",
                       related_metrics={"current_stock": 3, "daily_sales_avg": 2.1, "days_until_out": 1.5, "suggested_order": 50}),
            Suggestion(store_id=store.id, suggestion_type="price_adjustment",
                       title="价格调整建议：机械键盘青轴", priority="medium",
                       description="对比同品类，机械键盘青轴定价¥399处于中位数，建议上调至¥429-449。该商品评价4.8星，具备提价空间。",
                       data_source="sales_analyzer",
                       related_metrics={"current_price": 399, "suggested_price": 439, "competitor_avg": 425, "rating": 4.8}),
            Suggestion(store_id=store.id, suggestion_type="marketing_campaign",
                       title="营销活动建议：夏季清凉专题", priority="high",
                       description="夏季来临，清凉商品搜索量环比上升200%。建议策划「夏日清凉节」专题活动，配合满减优惠提升转化。",
                       data_source="trend_analyzer",
                       related_metrics={"search_volume_change": 200, "suggested_discount": 15, "estimated_revenue_boost": 35}),
            Suggestion(store_id=store.id, suggestion_type="inventory_optimization",
                       title="库存优化：鼠标垫库存积压", priority="low",
                       description="鼠标垫大号电竞款当前库存300件，近30天仅售12件，库存周转慢。建议降价清仓或捆绑销售。",
                       data_source="inventory_analyzer",
                       related_metrics={"current_stock": 300, "monthly_sales": 12, "turnover_days": 750, "suggested_price": 19}),
        ]
        for sug in suggestions:
            db.add(sug)
        await db.flush()

        # 8. 创建复盘数据
        from app.models.retrospective import Retrospective
        now_utc = _utcnow()
        month_start = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        week_end = now_utc - timedelta(days=now_utc.weekday())
        week_start = week_end - timedelta(days=6)

        retrospectives = [
            Retrospective(store_id=store.id, period_type="monthly",
                period_start=last_month_start, period_end=last_month_end,
                data_summary={"total_revenue": 125680, "total_orders": 423, "avg_order_value": 297.0, "refund_rate": 3.2},
                metrics_snapshot={"total_products": 15, "active_stores": 1},
                comparisons={"revenue_change_pct": 15.3, "order_change_pct": 8.7, "avg_order_value_change_pct": 6.1, "refund_rate_change": -0.5},
                insights=["本月销售总额 ¥125,680，环比增长 15.3%", "电子品类贡献 58% 的营收",
                          "退款率降至 3.2%，售后表现改善", "客单价提升至 ¥297，连带销售策略有效"],
                action_items=["增加蓝牙耳机 Pro 的备货量", "优化退款流程降低退款率"],
                status="published", published_at=_utcnow() - timedelta(days=2)),
            Retrospective(store_id=store.id, period_type="weekly",
                period_start=week_start, period_end=week_end,
                data_summary={"total_revenue": 32450, "total_orders": 112, "avg_order_value": 289.7, "refund_rate": 2.8},
                metrics_snapshot={"total_products": 15, "active_stores": 1},
                comparisons={"revenue_change_pct": 5.2, "order_change_pct": 3.1, "avg_order_value_change_pct": 2.0, "refund_rate_change": -0.3},
                insights=["本周销售额 ¥32,450，环比增长 5.2%", "新品智能手表 S3 表现亮眼"],
                action_items=["跟进智能手表 S3 的用户评价", "准备夏季专题活动素材"],
                status="draft"),
        ]
        for retro in retrospectives:
            db.add(retro)
        await db.flush()

        await db.commit()
        print("[OK] 模拟数据生成完成！")
        print(f"   - 演示用户：demo@example.com / Demo1234!")
        print(f"   - 店铺：{store.name}、{shopee.name}、{lazada.name}")
        print(f"   - 商品：{len(products)} 个")
        print(f"   - 订单：{order_id - 10000} 个（过去 30 天）")
        print(f"   - 自动回复：{len(auto_replies)} 条")
        print(f"   - 自动化规则：{len(rules)} 条")
        print(f"   - 选品：{len(selections)} 个")
        print(f"   - 运营建议：{len(suggestions)} 条")
        print(f"   - 复盘记录：{len(retrospectives)} 条")
        print(f"\n现在打开 http://localhost:8000/ 查看效果")


if __name__ == "__main__":
    asyncio.run(seed())
