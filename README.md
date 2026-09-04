# Supply Chain Inventory & Demand Forecasting System

A full-stack application for multi-warehouse inventory tracking and demand
forecasting, built to reflect the manufacturing/supply-chain domain that
Birlasoft's engineering teams build for (enterprise apps, ERP, and supply
chain client solutions).

## Features

- **Multi-warehouse inventory tracking** — products, warehouses, stock levels
- **Automatic low-stock alerts** based on per-product reorder thresholds
- **Demand forecasting** — linear-regression-based 7-day forecast per product
  from historical order data (built with scikit-learn/numpy), including
  trend classification (increasing/decreasing/stable)
- **REST API** (Flask) with full CRUD for warehouses, products, inventory, and orders
- **Live dashboard** (HTML/JS + Chart.js) — stock summary cards, low-stock
  table, and an interactive forecast chart per product
- **6 automated tests** (pytest) covering CRUD, low-stock logic, and forecasting edge cases
- **Dockerized backend + CI pipeline** (GitHub Actions)
- **Seed script** generating 90 days of realistic synthetic demand data
  (trend + weekday seasonality + noise) so the forecast has real signal to work with

## Tech Stack

Python · Flask · Flask-SQLAlchemy · SQLite · scikit-learn · numpy · pytest ·
HTML/CSS/JavaScript · Chart.js · Docker · GitHub Actions

## Architecture

```
Browser dashboard (HTML/JS + Chart.js)
        │  REST calls (fetch)
        ▼
Flask REST API ──► SQLAlchemy ORM ──► SQLite (swappable to PostgreSQL)
        │
        └──► forecasting.py (scikit-learn LinearRegression on daily demand series)
```

## Running locally

```bash
cd backend
pip install -r requirements.txt
python seed.py          # generates demo warehouses/products/inventory/90-day order history
python app.py            # starts API on http://localhost:5000
```

Then open `frontend/index.html` in a browser (it calls the API at `localhost:5000`).

## Running with Docker

```bash
cd backend
docker build -t inventory-forecast-api .
docker run -p 5000:5000 inventory-forecast-api
```

## Running tests

```bash
cd backend
pytest -v
```

## Key API Endpoints

| Method | Endpoint                          | Description                          |
|--------|-------------------------------------|----------------------------------------|
| GET/POST | `/api/warehouses`                 | List / create warehouses             |
| GET/POST | `/api/products`                   | List / create products               |
| GET/POST | `/api/inventory`                  | List / add inventory records         |
| PATCH  | `/api/inventory/<id>`              | Update stock quantity                |
| GET    | `/api/inventory/low-stock`         | Get all items below reorder threshold |
| GET/POST | `/api/orders`                     | List / record demand (order) history |
| GET    | `/api/forecast/<product_id>`       | Get historical + forecasted demand   |
| GET    | `/api/dashboard/summary`           | Aggregated KPIs for the dashboard    |

## Design notes / trade-offs (useful for interview discussion)

- Chose **linear regression** over ARIMA/XGBoost for forecasting: simpler,
  fully explainable to a business stakeholder, and sufficient for a
  short-horizon (7-day) reorder-planning use case. The `forecasting.py`
  module is written so the model can be swapped without touching the API layer.
- SQLite is used for portability in this demo; `DATABASE_URL` env var makes
  it a one-line swap to PostgreSQL for production.
- CORS is enabled so the static frontend can be served independently of the API.
