"""生成模拟数据，让看板和 API 有数据可展示。

用法：
    docker-compose exec api python -m app.seed_data
"""
import asyncio
import random
from datetime import UTC, datetime, timedelta

from app.infrastructure.database import async_session
from app.models.store import Store
from app.models.product import Product
from app.models.order import Order
from app.models.customer import Customer


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

        # 1. 创建模拟店铺
        store = Store(
            name="我的淘宝店",
            platform_type="taobao",
            store_url="demo_taobao_shop",
            api_key="demo_key",
            api_secret="demo_secret",
            is_active=True,
        )
        db.add(store)
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
                created_at=datetime.now(UTC) - timedelta(days=random.randint(30, 90)),
            )
            db.add(product)
            products.append(product)
        await db.flush()

        # 3. 创建过去 30 天的订单
        now = datetime.now(UTC)
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

        await db.commit()
        print("[OK] 模拟数据生成完成！")
        print(f"   - 店铺：{store.name}")
        print(f"   - 商品：{len(products)} 个")
        print(f"   - 订单：{order_id - 10000} 个（过去 30 天）")
        print(f"\n现在打开 http://localhost:8000/ 查看效果")


if __name__ == "__main__":
    asyncio.run(seed())
