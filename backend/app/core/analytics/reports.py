import csv
import io
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.analytics.inventory import InventoryAnalyzer
from app.core.analytics.sales import SalesAnalyzer
from app.core.analytics.trends import TrendAnalyzer


class ReportGenerator:
    """Generates reports in various formats (CSV, JSON)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_sales_csv(self, days: int = 30, store_id: int | None = None) -> str:
        analyzer = SalesAnalyzer(self.db)
        metrics = await analyzer.analyze(days=days, store_id=store_id, granularity="day")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Period", "Revenue", "Order Count", "Discounts"])
        for entry in metrics.revenue_by_day:
            writer.writerow([
                entry["period"],
                entry["revenue"],
                entry["order_count"],
                entry["discounts"],
            ])
        writer.writerow([])
        writer.writerow(["Summary"])
        writer.writerow(["Total Revenue", metrics.total_revenue])
        writer.writerow(["Total Orders", metrics.order_count])
        writer.writerow(["Avg Order Value", metrics.avg_order_value])

        return output.getvalue()

    async def generate_inventory_csv(self, store_id: int | None = None, low_stock_threshold: int = 10) -> str:
        analyzer = InventoryAnalyzer(self.db)
        metrics = await analyzer.analyze(store_id=store_id, low_stock_threshold=low_stock_threshold)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Low Stock Items"])
        writer.writerow(["Product ID", "Title", "SKU", "Quantity"])
        for item in metrics.low_stock_items:
            writer.writerow([item["id"], item["title"], item["sku"], item["quantity"]])
        writer.writerow([])
        writer.writerow(["Summary"])
        writer.writerow(["Total Products", metrics.total_products])
        writer.writerow(["Low Stock", metrics.low_stock_count])
        writer.writerow(["Out of Stock", metrics.out_of_stock_count])

        return output.getvalue()
