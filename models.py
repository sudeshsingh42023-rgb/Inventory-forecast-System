from datetime import datetime
from extensions import db


class Warehouse(db.Model):
    __tablename__ = "warehouses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)

    inventory_records = db.relationship("InventoryRecord", backref="warehouse", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "location": self.location}


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    reorder_threshold = db.Column(db.Integer, default=20)

    inventory_records = db.relationship("InventoryRecord", backref="product", lazy=True)
    orders = db.relationship("Order", backref="product", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "unit_price": self.unit_price,
            "reorder_threshold": self.reorder_threshold,
        }


class InventoryRecord(db.Model):
    __tablename__ = "inventory_records"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey("warehouses.id"), nullable=False)
    quantity_on_hand = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "sku": self.product.sku if self.product else None,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse.name if self.warehouse else None,
            "quantity_on_hand": self.quantity_on_hand,
            "reorder_threshold": self.product.reorder_threshold if self.product else None,
            "low_stock": (
                self.quantity_on_hand < self.product.reorder_threshold
                if self.product
                else False
            ),
            "last_updated": self.last_updated.isoformat(),
        }


class Order(db.Model):
    """Represents an outbound customer/demand order used as historical
    demand signal for forecasting."""

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.Date, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "order_date": self.order_date.isoformat(),
        }
