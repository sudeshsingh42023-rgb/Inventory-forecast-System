"""
Lightweight demand forecasting for a single product using historical order
quantities. Uses linear regression over daily aggregated demand as a simple,
explainable baseline (fits well within an interview discussion of trade-offs
vs. more complex models like ARIMA/XGBoost).
"""

from collections import defaultdict
from datetime import timedelta

import numpy as np
from sklearn.linear_model import LinearRegression


def forecast_demand(orders: list, horizon_days: int = 7):
    """
    orders: list of dicts with 'order_date' (date) and 'quantity' (int)
    Returns: dict with historical daily series, predicted next `horizon_days`
    values, and simple trend metadata.
    """
    if not orders:
        return {
            "history": [],
            "forecast": [],
            "trend": "insufficient_data",
        }

    daily_totals = defaultdict(int)
    for o in orders:
        daily_totals[o["order_date"]] += o["quantity"]

    sorted_dates = sorted(daily_totals.keys())
    start_date = sorted_dates[0]

    # Build a continuous daily series (fill gaps with 0 demand)
    end_date = sorted_dates[-1]
    all_dates = []
    d = start_date
    while d <= end_date:
        all_dates.append(d)
        d += timedelta(days=1)

    y = np.array([daily_totals.get(d, 0) for d in all_dates], dtype=float)
    X = np.arange(len(y)).reshape(-1, 1)

    if len(y) < 2:
        avg = float(y.mean())
        forecast_values = [avg] * horizon_days
        trend = "insufficient_data"
    else:
        model = LinearRegression()
        model.fit(X, y)
        future_X = np.arange(len(y), len(y) + horizon_days).reshape(-1, 1)
        forecast_values = model.predict(future_X).clip(min=0).tolist()
        trend = "increasing" if model.coef_[0] > 0.05 else (
            "decreasing" if model.coef_[0] < -0.05 else "stable"
        )

    history = [
        {"date": d.isoformat(), "quantity": int(daily_totals.get(d, 0))}
        for d in all_dates
    ]
    forecast = [
        {
            "date": (end_date + timedelta(days=i + 1)).isoformat(),
            "predicted_quantity": round(max(0, v), 1),
        }
        for i, v in enumerate(forecast_values)
    ]

    return {"history": history, "forecast": forecast, "trend": trend}
