import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app import create_app
from extensions import db


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_create_warehouse_and_product(client):
    wh = client.post("/api/warehouses", json={"name": "Pune DC", "location": "Pune"})
    assert wh.status_code == 201
    warehouse_id = wh.get_json()["id"]

    prod = client.post(
        "/api/products",
        json={"sku": "SKU-1", "name": "Widget", "category": "Parts", "unit_price": 100, "reorder_threshold": 10},
    )
    assert prod.status_code == 201
    product_id = prod.get_json()["id"]

    inv = client.post(
        "/api/inventory",
        json={"product_id": product_id, "warehouse_id": warehouse_id, "quantity_on_hand": 5},
    )
    assert inv.status_code == 201
    assert inv.get_json()["low_stock"] is True


def test_low_stock_endpoint(client):
    wh = client.post("/api/warehouses", json={"name": "DC1", "location": "X"}).get_json()
    p1 = client.post("/api/products", json={"sku": "A", "name": "A", "category": "c", "unit_price": 1, "reorder_threshold": 20}).get_json()
    p2 = client.post("/api/products", json={"sku": "B", "name": "B", "category": "c", "unit_price": 1, "reorder_threshold": 5}).get_json()

    client.post("/api/inventory", json={"product_id": p1["id"], "warehouse_id": wh["id"], "quantity_on_hand": 3})
    client.post("/api/inventory", json={"product_id": p2["id"], "warehouse_id": wh["id"], "quantity_on_hand": 50})

    resp = client.get("/api/inventory/low-stock")
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["sku"] == "A"


def test_orders_and_forecast(client):
    p = client.post("/api/products", json={"sku": "F1", "name": "Forecasted Item", "category": "c", "unit_price": 1, "reorder_threshold": 5}).get_json()

    from datetime import date, timedelta
    base = date.today() - timedelta(days=10)
    for i in range(10):
        client.post(
            "/api/orders",
            json={"product_id": p["id"], "quantity": 5 + i, "order_date": (base + timedelta(days=i)).isoformat()},
        )

    resp = client.get(f"/api/forecast/{p['id']}?horizon_days=5")
    data = resp.get_json()
    assert len(data["forecast"]) == 5
    assert data["trend"] == "increasing"


def test_forecast_with_no_orders_returns_insufficient_data(client):
    p = client.post("/api/products", json={"sku": "F2", "name": "No Orders", "category": "c", "unit_price": 1}).get_json()
    resp = client.get(f"/api/forecast/{p['id']}")
    data = resp.get_json()
    assert data["trend"] == "insufficient_data"


def test_dashboard_summary(client):
    wh = client.post("/api/warehouses", json={"name": "DC", "location": "X"}).get_json()
    p = client.post("/api/products", json={"sku": "S1", "name": "Item", "category": "c", "unit_price": 10}).get_json()
    client.post("/api/inventory", json={"product_id": p["id"], "warehouse_id": wh["id"], "quantity_on_hand": 100})

    resp = client.get("/api/dashboard/summary")
    data = resp.get_json()
    assert data["total_products"] == 1
    assert data["total_units_on_hand"] == 100
    assert data["total_inventory_value"] == 1000.0
