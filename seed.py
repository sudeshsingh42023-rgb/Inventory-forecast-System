"""Seeds the database with sample warehouses, products, inventory, and
90 days of synthetic order history (with trend + weekly seasonality) so the
forecasting endpoint has something meaningful to work with."""

import random
from datetime import date, timedelta

from app import create_app
from extensions import db
from models import Warehouse, Product, InventoryRecord, Order

random.seed(42)

app = create_app()

WAREHOUSES = [
    ("Pune DC", "Pune, Maharashtra"),
    ("Bengaluru DC", "Bengaluru, Karnataka"),
    ("Noida DC", "Noida, Uttar Pradesh"),
]

PRODUCTS = [
    ("SKU-1001", "Industrial Bearing 6205", "Mechanical Components", 180.0, 50),
    ("SKU-1002", "Hydraulic Pump HP-200", "Fluid Systems", 4200.0, 10),
    ("SKU-1003", "PLC Control Module CM-9", "Automation", 8500.0, 8),
    ("SKU-1004", "Conveyor Belt Roller CB-30", "Material Handling", 650.0, 30),
    ("SKU-1005", "Safety Sensor SS-77", "Automation", 320.0, 40),
]


def run():
    with app.app_context():
        db.drop_all()
        db.create_all()

        warehouses = [Warehouse(name=n, location=l) for n, l in WAREHOUSES]
        db.session.add_all(warehouses)
        db.session.commit()

        products = [
            Product(sku=sku, name=name, category=cat, unit_price=price, reorder_threshold=thresh)
            for sku, name, cat, price, thresh in PRODUCTS
        ]
        db.session.add_all(products)
        db.session.commit()

        for p in products:
            for w in warehouses:
                db.session.add(
                    InventoryRecord(
                        product_id=p.id,
                        warehouse_id=w.id,
                        quantity_on_hand=random.randint(5, 120),
                    )
                )
        db.session.commit()

        # Synthetic 90-day demand history per product: base demand + trend + weekly seasonality + noise
        today = date.today()
        for idx, p in enumerate(products):
            base = 10 + idx * 4
            trend = 0.05 * (idx + 1)
            for day_offset in range(90, 0, -1):
                d = today - timedelta(days=day_offset)
                weekday_boost = 6 if d.weekday() < 5 else 1  # more demand on weekdays
                qty = max(
                    0,
                    int(
                        base
                        + trend * (90 - day_offset)
                        + weekday_boost
                        + random.gauss(0, 2)
                    ),
                )
                if qty > 0:
                    db.session.add(Order(product_id=p.id, quantity=qty, order_date=d))
        db.session.commit()

        print(f"Seeded {len(warehouses)} warehouses, {len(products)} products, "
              f"{InventoryRecord.query.count()} inventory records, "
              f"{Order.query.count()} historical orders.")


if __name__ == "__main__":
    run()
