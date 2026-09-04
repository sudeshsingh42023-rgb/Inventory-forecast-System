from datetime import datetime, date

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
from extensions import db
from models import Warehouse, Product, InventoryRecord, Order
from forecasting import forecast_demand


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)
    db.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def register_routes(app):

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    # ---------------- Warehouses ----------------
    @app.route("/api/warehouses", methods=["GET", "POST"])
    def warehouses():
        if request.method == "POST":
            data = request.get_json()
            wh = Warehouse(name=data["name"], location=data["location"])
            db.session.add(wh)
            db.session.commit()
            return jsonify(wh.to_dict()), 201
        return jsonify([w.to_dict() for w in Warehouse.query.all()])

    # ---------------- Products ----------------
    @app.route("/api/products", methods=["GET", "POST"])
    def products():
        if request.method == "POST":
            data = request.get_json()
            product = Product(
                sku=data["sku"],
                name=data["name"],
                category=data["category"],
                unit_price=data["unit_price"],
                reorder_threshold=data.get("reorder_threshold", 20),
            )
            db.session.add(product)
            db.session.commit()
            return jsonify(product.to_dict()), 201
        return jsonify([p.to_dict() for p in Product.query.all()])

    # ---------------- Inventory ----------------
    @app.route("/api/inventory", methods=["GET", "POST"])
    def inventory():
        if request.method == "POST":
            data = request.get_json()
            record = InventoryRecord(
                product_id=data["product_id"],
                warehouse_id=data["warehouse_id"],
                quantity_on_hand=data.get("quantity_on_hand", 0),
            )
            db.session.add(record)
            db.session.commit()
            return jsonify(record.to_dict()), 201

        warehouse_id = request.args.get("warehouse_id", type=int)
        query = InventoryRecord.query
        if warehouse_id:
            query = query.filter_by(warehouse_id=warehouse_id)
        return jsonify([r.to_dict() for r in query.all()])

    @app.route("/api/inventory/<int:record_id>", methods=["PATCH"])
    def update_inventory(record_id):
        record = InventoryRecord.query.get_or_404(record_id)
        data = request.get_json()
        if "quantity_on_hand" in data:
            record.quantity_on_hand = data["quantity_on_hand"]
        db.session.commit()
        return jsonify(record.to_dict())

    @app.route("/api/inventory/low-stock", methods=["GET"])
    def low_stock():
        records = InventoryRecord.query.all()
        low = [r.to_dict() for r in records if r.to_dict()["low_stock"]]
        return jsonify(low)

    # ---------------- Orders (demand history) ----------------
    @app.route("/api/orders", methods=["GET", "POST"])
    def orders():
        if request.method == "POST":
            data = request.get_json()
            order = Order(
                product_id=data["product_id"],
                quantity=data["quantity"],
                order_date=datetime.strptime(data["order_date"], "%Y-%m-%d").date(),
            )
            db.session.add(order)
            db.session.commit()
            return jsonify(order.to_dict()), 201

        product_id = request.args.get("product_id", type=int)
        query = Order.query
        if product_id:
            query = query.filter_by(product_id=product_id)
        return jsonify([o.to_dict() for o in query.order_by(Order.order_date).all()])

    # ---------------- Forecasting ----------------
    @app.route("/api/forecast/<int:product_id>", methods=["GET"])
    def forecast(product_id):
        horizon = request.args.get("horizon_days", default=7, type=int)
        product = Product.query.get_or_404(product_id)
        order_rows = (
            Order.query.filter_by(product_id=product_id)
            .order_by(Order.order_date)
            .all()
        )
        orders_data = [{"order_date": o.order_date, "quantity": o.quantity} for o in order_rows]
        result = forecast_demand(orders_data, horizon_days=horizon)
        result["product"] = product.to_dict()
        return jsonify(result)

    # ---------------- Dashboard summary ----------------
    @app.route("/api/dashboard/summary", methods=["GET"])
    def dashboard_summary():
        total_products = Product.query.count()
        total_warehouses = Warehouse.query.count()
        all_records = InventoryRecord.query.all()
        low_stock_count = sum(1 for r in all_records if r.to_dict()["low_stock"])
        total_units = sum(r.quantity_on_hand for r in all_records)
        inventory_value = sum(
            r.quantity_on_hand * (r.product.unit_price if r.product else 0)
            for r in all_records
        )
        return jsonify(
            {
                "total_products": total_products,
                "total_warehouses": total_warehouses,
                "low_stock_count": low_stock_count,
                "total_units_on_hand": total_units,
                "total_inventory_value": round(inventory_value, 2),
            }
        )


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
