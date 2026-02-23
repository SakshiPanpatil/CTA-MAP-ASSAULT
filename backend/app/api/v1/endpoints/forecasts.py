"""
Card 2 – Future Trends forecasting endpoint.
Best model per template determined from notebook competition:
  T1 (Incident Count)      → SARIMAX(0,1,1)×(0,1,1,12)   MAPE 11.6%
  T2 (Total Injuries)      → SARIMAX(1,1,1)×(0,1,1,12)   MAPE 15.8%
  T3 (Operator Injuries)   → ARIMA(0,1,1)                 MAPE 18.5%
  T4 (Rider Injuries)      → Prophet(cp=0.1, sp=10.0)     MAPE 15.3%
  T5 (Seasonal)            → derived from T1 model
  T6 (Year-over-Year)      → derived from T1 model
"""
import collections
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sklearn.metrics import mean_absolute_error
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

from ....core.config import settings
from ....core.security import get_current_user
from ....models.auth import User

router = APIRouter()

# ── Template definitions ─────────────────────────────────────────────────────
TEMPLATES = {
    1: {"name": "Incident Count Forecast",    "metric": "count",                              "y_label": "Incidents/Month",  "model": "sarimax", "order": (0,1,1), "seasonal_order": (0,1,1,12), "style": "forecast"},
    2: {"name": "Total Injuries Forecast",     "metric": "Total Injuries",                     "y_label": "Injuries/Month",   "model": "sarimax", "order": (1,1,1), "seasonal_order": (0,1,1,12), "style": "forecast"},
    3: {"name": "Operator Injuries Forecast",  "metric": "Transit Vehicle Operator Injuries",  "y_label": "Injuries/Month",   "model": "arima",   "order": (0,1,1),                               "style": "forecast"},
    4: {"name": "Rider Injuries Forecast",     "metric": "Transit Vehicle Rider Injuries",     "y_label": "Injuries/Month",   "model": "prophet", "cp": 0.1, "sp": 10.0,                          "style": "forecast"},
    5: {"name": "Monthly Seasonality",         "metric": "count",                              "y_label": "Avg Incidents",    "model": "sarimax", "order": (0,1,1), "seasonal_order": (0,1,1,12), "style": "seasonal"},
    6: {"name": "Year-over-Year + Forecast",   "metric": "count",                              "y_label": "Incidents",        "model": "sarimax", "order": (0,1,1), "seasonal_order": (0,1,1,12), "style": "yoy"},
}

MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Columns allowed for custom filtering
FILTER_COLUMNS = [
    "Event Category",
    "Event Type",
    "Event Type Group",
    "Location Type",
    "Rail/Bus/Ferry",
    "Safety/Security",
    "Transit Worker Type",
    "Transit Worker Assault Detail Type",
    "Intentional (Y/N)",
    "Weather",
    "Lighting",
]

# Metrics supported for custom forecasting
CUSTOM_METRICS: dict[str, str] = {
    "count":                                        "Incidents/Month",
    "Total Injuries":                               "Injuries/Month",
    "Total Fatalities":                             "Fatalities/Month",
    "Total Serious Injuries":                       "Serious Injuries/Month",
    "Transit Vehicle Rider Injuries":               "Rider Injuries/Month",
    "Transit Vehicle Rider Serious Injuries":       "Rider Serious Injuries/Month",
    "Transit Vehicle Rider Fatalities":             "Rider Fatalities/Month",
    "Transit Vehicle Operator Injuries":            "Operator Injuries/Month",
    "Transit Vehicle Operator Serious Injuries":    "Operator Serious Injuries/Month",
    "Transit Vehicle Operator Fatalities":          "Operator Fatalities/Month",
    "Non-Operator Transit Employee Injuries":       "Non-Op Employee Injuries/Month",
    "Non-Operator Transit Employee Serious Injuries": "Non-Op Employee Serious Injuries/Month",
    "People Waiting or Leaving Injuries":           "Waiting/Leaving Injuries/Month",
    "People Waiting or Leaving Fatalities":         "Waiting/Leaving Fatalities/Month",
}

# Hyperparameter search grids
_ARIMA_ORDERS = [(0,1,1), (1,1,1), (0,1,2), (2,1,1), (1,1,0)]
_SARIMAX_CONFIGS = [
    ((0,1,1), (0,1,1,12)),
    ((1,1,1), (0,1,1,12)),
    ((0,1,2), (0,1,1,12)),
    ((1,1,0), (1,0,0,12)),
]
_PROPHET_CONFIGS = [(0.05, 10.0), (0.1, 10.0), (0.3, 10.0), (0.1, 5.0), (0.3, 5.0)]

# In-memory cache: cache_key → result
_cache: dict[tuple, Any] = {}


# ── Data loading ─────────────────────────────────────────────────────────────
def _load_series(metric: str, since: str = "2016") -> pd.Series:
    df = pd.read_csv(str(settings.assault_data_file), low_memory=False)

    def _parse(d):
        if pd.isna(d): return pd.NaT
        try:    return pd.to_datetime(d, format="%Y %B %d")
        except: return pd.to_datetime(d, errors="coerce")

    df["parsed_date"] = df["Event Date"].apply(_parse)
    df = df[df["parsed_date"].notna()].copy()
    df["ym"] = df["parsed_date"].dt.to_period("M")

    if metric == "count":
        s = df.groupby("ym").size().to_timestamp()
    else:
        df[metric] = pd.to_numeric(df.get(metric, 0), errors="coerce").fillna(0)
        s = df.groupby("ym")[metric].sum().to_timestamp()

    return s[s.index >= since]


# ── Model runners ─────────────────────────────────────────────────────────────
def _mape(actual, predicted):
    a, p = np.array(actual, float), np.array(predicted, float)
    return float(np.mean(np.abs((a - p) / np.where(a == 0, 1, a))) * 100)


def _base_dict(series, train_len, test_actual, test_pred, fc_vals, lower, upper, fc_dates, mae, mape, model_name):
    train_end = series.index[train_len - 1]
    return {
        "historical_dates":  series.index.strftime("%Y-%m-%d").tolist(),
        "historical_values": [float(v) for v in series.values],
        "train_end_date":    train_end.strftime("%Y-%m-%d"),
        "train_len":         train_len,
        "test_dates":        series.index[train_len:].strftime("%Y-%m-%d").tolist(),
        "test_actual":       [float(v) for v in test_actual],
        "test_forecast":     [float(v) for v in test_pred],
        "forecast_dates":    fc_dates.strftime("%Y-%m-%d").tolist(),
        "forecast_values":   [max(0.0, float(v)) for v in fc_vals],
        "forecast_lower":    [max(0.0, float(v)) for v in lower],
        "forecast_upper":    [max(0.0, float(v)) for v in upper],
        "mae":               round(float(mae), 2),
        "mape":              round(mape, 1),
        "model_name":        model_name,
    }


def _run_sarimax(series, order, seasonal_order, periods):
    train, test = series[:-6], series[-6:]
    val = SARIMAX(train, order=order, seasonal_order=seasonal_order).fit(disp=False)
    test_fc = val.forecast(steps=6)
    mae = mean_absolute_error(test, test_fc)

    full = SARIMAX(series, order=order, seasonal_order=seasonal_order).fit(disp=False)
    fc   = full.get_forecast(steps=periods)
    conf = fc.conf_int()
    fcd  = pd.date_range(start=series.index[-1] + pd.DateOffset(months=1), periods=periods, freq="MS")

    return _base_dict(series, len(train), test.values, test_fc.values,
                      fc.predicted_mean.values, conf.iloc[:,0].values, conf.iloc[:,1].values,
                      fcd, mae, _mape(test.values, test_fc.values),
                      f"SARIMAX{order}×{seasonal_order}")


def _run_arima(series, order, periods):
    train, test = series[:-6], series[-6:]
    val = ARIMA(train, order=order).fit()
    test_fc = val.forecast(steps=6)
    mae = mean_absolute_error(test, test_fc)

    full = ARIMA(series, order=order).fit()
    fc   = full.get_forecast(steps=periods)
    conf = fc.conf_int()
    fcd  = pd.date_range(start=series.index[-1] + pd.DateOffset(months=1), periods=periods, freq="MS")

    return _base_dict(series, len(train), test.values, test_fc.values,
                      fc.predicted_mean.values, conf.iloc[:,0].values, conf.iloc[:,1].values,
                      fcd, mae, _mape(test.values, test_fc.values),
                      f"ARIMA{order}")


def _run_prophet(series, cp, sp, periods):
    from prophet import Prophet  # lazy import — Prophet is heavy

    pdf = series.reset_index()
    pdf.columns = ["ds", "y"]
    train_df, test_df = pdf.iloc[:-6], pdf.iloc[-6:]

    def _fit(data):
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False,
                    daily_seasonality=False, changepoint_prior_scale=cp,
                    seasonality_prior_scale=sp, interval_width=0.80)
        m.fit(data)
        return m

    m_val = _fit(train_df)
    test_fc_vals = m_val.predict(m_val.make_future_dataframe(periods=6, freq="MS")).tail(6)["yhat"].values
    mae = mean_absolute_error(test_df["y"].values, test_fc_vals)

    m_full = _fit(pdf)
    pred   = m_full.predict(m_full.make_future_dataframe(periods=periods, freq="MS"))
    fc_rows = pred.tail(periods)
    fcd = pd.date_range(start=series.index[-1] + pd.DateOffset(months=1), periods=periods, freq="MS")

    return _base_dict(series, len(series) - 6, series.iloc[-6:].values, test_fc_vals,
                      fc_rows["yhat"].values, fc_rows["yhat_lower"].values, fc_rows["yhat_upper"].values,
                      fcd, mae, _mape(test_df["y"].values, test_fc_vals),
                      f"Prophet(cp={cp},sp={sp})")


# ── Seasonal / YoY extras ─────────────────────────────────────────────────────
def _add_seasonal(result: dict) -> dict:
    hist_dates  = pd.to_datetime(result["historical_dates"])
    hist_vals   = result["historical_values"]
    fc_dates    = pd.to_datetime(result["forecast_dates"])
    fc_vals     = result["forecast_values"]

    by_month: dict = collections.defaultdict(list)
    for d, v in zip(hist_dates, hist_vals):
        by_month[d.month].append(v)
    hist_avg = [round(float(np.mean(by_month.get(m, [0]))), 2) for m in range(1, 13)]

    fc_by: dict = collections.defaultdict(list)
    for d, v in zip(fc_dates, fc_vals):
        fc_by[d.month].append(v)
    fc_avg = [round(float(np.mean(fc_by[m])), 2) if fc_by.get(m) else None for m in range(1, 13)]

    result["seasonal"] = {"month_names": MONTH_NAMES, "hist_avg": hist_avg, "fc_avg": fc_avg}
    return result


def _add_yoy(result: dict) -> dict:
    hist_dates = pd.to_datetime(result["historical_dates"])
    hist_vals  = result["historical_values"]
    fc_dates   = pd.to_datetime(result["forecast_dates"])
    fc_vals    = result["forecast_values"]

    df = pd.DataFrame({"d": hist_dates, "v": hist_vals})
    df["yr"] = df["d"].dt.year
    df["mo"] = df["d"].dt.month

    years_data = {}
    for yr, grp in df.groupby("yr"):
        row = {m: None for m in range(1, 13)}
        for _, r in grp.iterrows():
            row[int(r["mo"])] = round(float(r["v"]), 2)
        years_data[str(yr)] = [row[m] for m in range(1, 13)]

    fc_by: dict = collections.defaultdict(list)
    for d, v in zip(fc_dates, fc_vals):
        fc_by[d.month].append(v)
    fc_avg = [round(float(np.mean(fc_by[m])), 2) if fc_by.get(m) else None for m in range(1, 13)]

    result["yoy"] = {"month_names": MONTH_NAMES, "years_data": years_data, "fc_avg": fc_avg}
    return result


# ── Filtered series loader (for custom endpoint) ──────────────────────────────
def _load_series_filtered(
    metric: str,
    since: str = "2016",
    filter_col: str | None = None,
    filter_val: str | None = None,
) -> pd.Series:
    df = pd.read_csv(str(settings.assault_data_file), low_memory=False)

    def _parse(d):
        if pd.isna(d): return pd.NaT
        try:    return pd.to_datetime(d, format="%Y %B %d")
        except: return pd.to_datetime(d, errors="coerce")

    df["parsed_date"] = df["Event Date"].apply(_parse)
    df = df[df["parsed_date"].notna()].copy()
    df["ym"] = df["parsed_date"].dt.to_period("M")

    if filter_col and filter_val and filter_col in df.columns:
        df = df[df[filter_col].astype(str) == filter_val]

    if metric == "count":
        s = df.groupby("ym").size().to_timestamp()
    else:
        df[metric] = pd.to_numeric(df.get(metric, 0), errors="coerce").fillna(0)
        s = df.groupby("ym")[metric].sum().to_timestamp()

    return s[s.index >= since]


# ── Model competition (hyperparameter search across all families) ──────────────
def _run_model_competition(series: pd.Series, periods: int) -> list[dict]:
    """Try every config for ARIMA / SARIMAX / Prophet; return all results sorted by MAE."""
    if len(series) < 24:
        raise ValueError(f"Only {len(series)} months available — need at least 24.")

    results: list[dict] = []

    for order in _ARIMA_ORDERS:
        try:
            r = _run_arima(series, order, periods)
            r["model_family"] = "ARIMA"
            results.append(r)
        except Exception:
            pass

    for order, seasonal in _SARIMAX_CONFIGS:
        try:
            r = _run_sarimax(series, order, seasonal, periods)
            r["model_family"] = "SARIMAX"
            results.append(r)
        except Exception:
            pass

    for cp, sp in _PROPHET_CONFIGS:
        try:
            r = _run_prophet(series, cp, sp, periods)
            r["model_family"] = "Prophet"
            results.append(r)
        except Exception:
            pass

    if not results:
        raise ValueError("All models failed to converge on this series.")

    results.sort(key=lambda x: x["mae"])
    return results


# ── Custom: filter-values helper ───────────────────────────────────────────────
@router.get("/filter-values")
def get_filter_values(
    col: str = Query(...),
    _: User = Depends(get_current_user),
):
    if col not in FILTER_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Column '{col}' is not supported for filtering.")
    df = pd.read_csv(str(settings.assault_data_file), low_memory=False)
    if col not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{col}' not found in dataset.")
    values = sorted(df[col].dropna().astype(str).unique().tolist())
    return {"column": col, "values": values}


# ── Custom forecast (model competition) ───────────────────────────────────────
@router.get("/custom")
def run_custom_forecast(
    metric: str = Query("count"),
    since: str = Query("2016"),
    periods: int = Query(12, ge=6, le=24),
    filter_col: str | None = Query(None),
    filter_val: str | None = Query(None),
    _: User = Depends(get_current_user),
):
    if metric not in CUSTOM_METRICS:
        raise HTTPException(status_code=400, detail=f"Metric '{metric}' is not supported.")
    if filter_col and filter_col not in FILTER_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Filter column '{filter_col}' is not allowed.")

    cache_key = ("custom", metric, since, periods, filter_col, filter_val)
    if cache_key in _cache:
        return _cache[cache_key]

    series = _load_series_filtered(metric, since, filter_col, filter_val)

    if len(series) < 24:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Only {len(series)} months of data available for this selection. "
                "Need at least 24. Try a broader date range or a less specific filter."
            ),
        )

    all_results = _run_model_competition(series, periods)
    best = all_results[0]

    comparison = [
        {
            "model_name":   r["model_name"],
            "model_family": r.get("model_family", ""),
            "mae":          r["mae"],
            "mape":         r["mape"],
        }
        for r in all_results
    ]

    label = metric if metric != "count" else "Incident Count"
    filter_label = f" [{filter_col}: {filter_val}]" if filter_col and filter_val else ""

    result: dict = {
        "metric":           metric,
        "filter_col":       filter_col,
        "filter_val":       filter_val,
        "y_label":          CUSTOM_METRICS[metric],
        "chart_title":      f"{label} Forecast{filter_label}",
        "chart_style":      "forecast",
        "forecast_periods": periods,
        "comparison":       comparison,
        **{k: v for k, v in best.items() if k != "model_family"},
    }

    _cache[cache_key] = result
    return result


# ── Preset template endpoint ───────────────────────────────────────────────────
@router.get("/{template_id}")
def get_forecast(
    template_id: int,
    periods: int = Query(12, ge=6, le=24),
    _: User = Depends(get_current_user),
):
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    cache_key = (template_id, periods)
    if cache_key in _cache:
        return _cache[cache_key]

    meta   = TEMPLATES[template_id]
    series = _load_series(meta["metric"])

    if meta["model"] == "sarimax":
        data = _run_sarimax(series, meta["order"], meta["seasonal_order"], periods)
    elif meta["model"] == "arima":
        data = _run_arima(series, meta["order"], periods)
    else:
        data = _run_prophet(series, meta["cp"], meta["sp"], periods)

    result: dict = {
        "template_id":      template_id,
        "template_name":    meta["name"],
        "y_label":          meta["y_label"],
        "chart_style":      meta["style"],
        "forecast_periods": periods,
        **data,
    }

    if meta["style"] == "seasonal":
        result = _add_seasonal(result)
    elif meta["style"] == "yoy":
        result = _add_yoy(result)

    _cache[cache_key] = result
    return result
