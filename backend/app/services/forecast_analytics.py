"""
Forecast Analytics Service - SARIMAX Time Series Forecasting
Integrates ML-based forecasting into PDF reports with professional visualizations.
"""
from __future__ import annotations

import io
import warnings
from datetime import datetime
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.metrics import mean_absolute_error, mean_squared_error

matplotlib.use("Agg")
warnings.filterwarnings('ignore')

# Professional color scheme
COLORS = {
    "primary": "#0c5ed7",
    "danger": "#b71c1c",
    "warning": "#fb8c00",
    "success": "#1f8b4c",
    "forecast": "#9c27b0",
    "confidence": "#e1bee7",
}


def prepare_time_series_data(assaults: list[dict[str, Any]]) -> tuple[pd.Series, dict]:
    """
    Prepare assault data for time series forecasting.

    Returns:
        (monthly_series, metadata) - Series indexed by month and metadata dict
    """
    # Parse dates
    dates = []
    for assault in assaults:
        date_str = assault.get("event_date", "")
        try:
            parts = str(date_str).strip().split()
            if len(parts) >= 3:
                year = int(parts[0])
                month_map = {
                    "january": 1, "february": 2, "march": 3, "april": 4,
                    "may": 5, "june": 6, "july": 7, "august": 8,
                    "september": 9, "october": 10, "november": 11, "december": 12,
                }
                month = month_map.get(parts[1].lower(), 1)
                day = int(parts[2])
                dates.append(pd.Timestamp(year, month, day))
        except (ValueError, AttributeError, KeyError, IndexError):
            continue

    if not dates:
        return None, {}

    # Create monthly series
    df = pd.DataFrame({'date': dates})
    df['year_month'] = df['date'].dt.to_period('M')
    monthly_counts = df.groupby('year_month').size()
    monthly_series = monthly_counts.to_timestamp()

    # Fill missing months with 0 to create continuous time series
    if len(monthly_series) > 0:
        full_range = pd.date_range(
            start=monthly_series.index.min(),
            end=monthly_series.index.max(),
            freq='MS'  # Month start frequency
        )
        monthly_series = monthly_series.reindex(full_range, fill_value=0)

    # Metadata
    metadata = {
        'total_incidents': len(assaults),
        'total_months': len(monthly_series),
        'date_range_start': monthly_series.index.min() if len(monthly_series) > 0 else None,
        'date_range_end': monthly_series.index.max() if len(monthly_series) > 0 else None,
        'avg_monthly': monthly_series.mean() if len(monthly_series) > 0 else 0,
        'max_monthly': monthly_series.max() if len(monthly_series) > 0 else 0,
        'min_monthly': monthly_series.min() if len(monthly_series) > 0 else 0,
    }

    return monthly_series, metadata


def train_sarimax_forecast(monthly_series: pd.Series, forecast_periods: int = 6) -> dict | None:
    """
    Train SARIMAX model (best performer) and generate forecast.

    Args:
        monthly_series: Monthly incident counts
        forecast_periods: Months to forecast ahead

    Returns:
        Dictionary with model results and metrics, or None if insufficient data
    """
    if len(monthly_series) < 12:  # Reduced from 24 to 12 months
        return None

    # Split train/test (adaptive based on data length)
    test_months = min(6, max(3, len(monthly_series) // 4))  # 3-6 months for testing
    train_size = len(monthly_series) - test_months
    train = monthly_series[:train_size]
    test = monthly_series[train_size:]

    try:
        # SARIMAX with best parameters: ((0,1,1), (0,1,1,12))
        model = SARIMAX(train, order=(0, 1, 1), seasonal_order=(0, 1, 1, 12))
        fitted = model.fit(disp=False, maxiter=100)

        # Forecast
        forecast_obj = fitted.get_forecast(steps=len(test) + forecast_periods)
        forecast_df = forecast_obj.summary_frame(alpha=0.20)  # 80% confidence

        # Test metrics
        test_forecast = forecast_df['mean'].iloc[:len(test)]
        mae = mean_absolute_error(test, test_forecast)
        rmse = np.sqrt(mean_squared_error(test, test_forecast))
        mape = np.mean(np.abs((test - test_forecast) / test)) * 100

        # Future forecast
        future_forecast = forecast_df['mean'].iloc[len(test):]
        future_lower = forecast_df['mean_ci_lower'].iloc[len(test):]
        future_upper = forecast_df['mean_ci_upper'].iloc[len(test):]

        # Future dates
        future_dates = pd.date_range(
            start=monthly_series.index[-1] + pd.DateOffset(months=1),
            periods=forecast_periods,
            freq='MS'
        )

        return {
            'model': fitted,
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'forecast_values': future_forecast.values,
            'forecast_lower': future_lower.values,
            'forecast_upper': future_upper.values,
            'forecast_dates': future_dates,
            'historical': monthly_series,
            'train': train,
            'test': test,
            'test_forecast': test_forecast.values,
        }
    except Exception:
        return None


def create_enhanced_forecast_plot(
    result: dict,
    title: str = "Location",
    show_metrics: bool = True
) -> io.BytesIO:
    """
    Create professional forecast plot with annotations and metrics.

    Features:
    - Historical data with trend
    - Test forecast validation
    - Future forecast with confidence intervals
    - Metric scores displayed
    - Annotations explaining key trends
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('#f8f9fa')

    historical = result['historical']
    forecast_dates = result['forecast_dates']
    forecast_values = result['forecast_values']
    forecast_lower = result['forecast_lower']
    forecast_upper = result['forecast_upper']

    # Historical data
    ax.plot(historical.index, historical.values,
           'o-', color=COLORS['primary'], linewidth=2.5, markersize=6,
           label='Historical Data', zorder=3)

    # Add trend line for historical data
    if len(historical) >= 3:
        x_numeric = np.arange(len(historical))
        z = np.polyfit(x_numeric, historical.values, 1)
        p = np.poly1d(z)
        ax.plot(historical.index, p(x_numeric),
               '--', color=COLORS['success'], linewidth=2, alpha=0.7,
               label=f'Trend Line ({"↑" if z[0] > 0 else "↓"})', zorder=2)

    # Test forecast (validation)
    test_dates = historical.index[len(result['train']):]
    ax.plot(test_dates, result['test_forecast'],
           's-', color=COLORS['warning'], linewidth=2, markersize=5,
           label='Model Validation', alpha=0.8, zorder=2)

    # Future forecast
    ax.plot(forecast_dates, forecast_values,
           '^--', color=COLORS['forecast'], linewidth=3, markersize=7,
           label='Forecast (SARIMAX)', zorder=4)

    # Confidence interval
    ax.fill_between(forecast_dates,
                     forecast_lower,
                     forecast_upper,
                     alpha=0.25, color=COLORS['confidence'],
                     label='80% Confidence Interval')

    # TODAY line
    ax.axvline(x=historical.index[-1], color='gray', linestyle=':', linewidth=2.5, alpha=0.6, zorder=1)
    y_pos = ax.get_ylim()[1] * 0.95
    ax.text(historical.index[-1], y_pos, '  TODAY',
           ha='left', va='top', fontsize=11, color='gray',
           fontweight='bold', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

    # Calculate trend
    hist_avg = historical.mean()
    fcst_avg = forecast_values.mean()
    change_pct = ((fcst_avg - hist_avg) / hist_avg) * 100

    # Trend annotation
    trend_color = COLORS['danger'] if change_pct > 10 else COLORS['success'] if change_pct < -10 else COLORS['warning']
    trend_text = f"{'↑' if change_pct > 0 else '↓'} {abs(change_pct):.1f}% trend"

    ax.annotate(
        trend_text,
        xy=(forecast_dates[-1], forecast_values[-1]),
        xytext=(20, 20), textcoords='offset points',
        fontsize=11, fontweight='bold', color=trend_color,
        bbox=dict(boxstyle='round,pad=0.6', facecolor='white', edgecolor=trend_color, linewidth=2),
        arrowprops=dict(arrowstyle='->', color=trend_color, lw=2)
    )

    # Metrics box (if enabled)
    if show_metrics:
        metrics_text = (
            f"Model: SARIMAX\n"
            f"MAE: {result['mae']:.2f}\n"
            f"RMSE: {result['rmse']:.2f}\n"
            f"MAPE: {result['mape']:.1f}%"
        )
        ax.text(0.02, 0.98, metrics_text,
               transform=ax.transAxes,
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round,pad=0.8', facecolor='white',
                        edgecolor=COLORS['primary'], linewidth=1.5, alpha=0.95),
               family='monospace')

    # Styling
    ax.set_title(f'Forecast Analysis - {title}',
                fontsize=16, fontweight='bold', pad=20, color='#0b2c67')
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Monthly Incidents', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10, framealpha=0.95, edgecolor='gray')
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()

    return buf


def create_seasonal_decomposition_plot(monthly_series: pd.Series, title: str = "Location") -> io.BytesIO | None:
    """
    Create seasonal decomposition plot showing trend, seasonality, and residuals.
    """
    if len(monthly_series) < 12:  # Reduced from 24 to 12 months
        return None

    try:
        decomposition = seasonal_decompose(monthly_series, model='additive', period=12)

        fig, axes = plt.subplots(4, 1, figsize=(14, 11))
        fig.patch.set_facecolor('white')

        # Original
        decomposition.observed.plot(ax=axes[0], color=COLORS['primary'], linewidth=2)
        axes[0].set_title(f'Seasonal Decomposition Analysis - {title}',
                         fontsize=14, fontweight='bold', color='#0b2c67')
        axes[0].set_ylabel('Observed', fontsize=11, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        axes[0].set_facecolor('#f8f9fa')

        # Trend
        decomposition.trend.plot(ax=axes[1], color=COLORS['warning'], linewidth=2.5)
        axes[1].set_ylabel('Trend', fontsize=11, fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        axes[1].set_facecolor('#f8f9fa')

        # Calculate trend direction
        trend_data = decomposition.trend.dropna()
        trend_change = ((trend_data.iloc[-1] - trend_data.iloc[0]) / trend_data.iloc[0]) * 100
        trend_label = f"{'Increasing' if trend_change > 0 else 'Decreasing'} ({trend_change:+.1f}%)"
        axes[1].text(0.02, 0.98, trend_label, transform=axes[1].transAxes,
                    fontsize=10, verticalalignment='top', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))

        # Seasonal
        decomposition.seasonal.plot(ax=axes[2], color=COLORS['success'], linewidth=2)
        axes[2].set_ylabel('Seasonal', fontsize=11, fontweight='bold')
        axes[2].grid(True, alpha=0.3)
        axes[2].set_facecolor('#f8f9fa')

        # Peak season
        seasonal_data = decomposition.seasonal
        peak_month = seasonal_data.idxmax().month_name()
        low_month = seasonal_data.idxmin().month_name()
        seasonal_label = f"Peak: {peak_month} | Low: {low_month}"
        axes[2].text(0.02, 0.98, seasonal_label, transform=axes[2].transAxes,
                    fontsize=10, verticalalignment='top', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))

        # Residual
        decomposition.resid.plot(ax=axes[3], color=COLORS['danger'], linewidth=1, alpha=0.7)
        axes[3].set_ylabel('Residual', fontsize=11, fontweight='bold')
        axes[3].set_xlabel('Date', fontsize=11, fontweight='bold')
        axes[3].grid(True, alpha=0.3)
        axes[3].set_facecolor('#f8f9fa')

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close()

        return buf
    except Exception:
        return None


def generate_why_analysis(result: dict, monthly_series: pd.Series, title: str = "location") -> dict:
    """
    Generate hardcoded "WHY" analysis explaining current and future trends.

    Returns:
        Dictionary with 'current_why' and 'future_why' explanations
    """
    # Calculate metrics
    hist_avg = monthly_series.mean()
    fcst_avg = result['forecast_values'].mean()
    change_pct = ((fcst_avg - hist_avg) / hist_avg) * 100

    # Historical trend analysis
    recent_3mo = monthly_series.iloc[-3:].mean()
    older_3mo = monthly_series.iloc[-6:-3].mean()
    recent_trend = ((recent_3mo - older_3mo) / older_3mo) * 100 if older_3mo > 0 else 0

    # Seasonal analysis
    monthly_avg_by_month = {}
    for idx, val in monthly_series.items():
        month = idx.month
        if month not in monthly_avg_by_month:
            monthly_avg_by_month[month] = []
        monthly_avg_by_month[month].append(val)

    seasonal_pattern = {m: np.mean(vals) for m, vals in monthly_avg_by_month.items()}
    peak_month = max(seasonal_pattern, key=seasonal_pattern.get)
    low_month = min(seasonal_pattern, key=seasonal_pattern.get)

    month_names = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
                   7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}

    # WHY CURRENT TRENDS
    current_why = []

    if recent_trend > 15:
        current_why.append(f"Recent 3-month period shows <b>significant increase</b> ({recent_trend:+.1f}%) compared to previous quarter, indicating escalating safety concerns.")
    elif recent_trend < -15:
        current_why.append(f"Recent 3-month period shows <b>notable improvement</b> ({recent_trend:+.1f}%) compared to previous quarter, suggesting effective interventions.")
    else:
        current_why.append(f"Incident levels have remained <b>relatively stable</b> ({recent_trend:+.1f}% change) in recent months.")

    if hist_avg > 5:
        current_why.append(f"This {title} experiences <b>above-average incident frequency</b> ({hist_avg:.1f} per month), indicating a persistent safety challenge requiring ongoing attention.")
    elif hist_avg > 2:
        current_why.append(f"Moderate incident frequency ({hist_avg:.1f} per month) suggests <b>standard urban transit challenges</b> typical of high-traffic areas.")
    else:
        current_why.append(f"Low incident frequency ({hist_avg:.1f} per month) indicates this is a <b>relatively safe area</b> with sporadic incidents.")

    current_why.append(f"Historical data shows <b>seasonal variation</b> with peak incidents in {month_names[peak_month]} and lowest in {month_names[low_month]}, likely correlated with ridership patterns and environmental factors.")

    # WHY FUTURE TRENDS
    future_why = []

    if change_pct > 20:
        future_why.append(f"Model predicts <b>significant increase</b> ({change_pct:+.1f}%) based on accelerating trend patterns observed in recent months and historical seasonal cycles.")
        future_why.append("This sharp upward trajectory suggests <b>urgent intervention required</b> to reverse the trend. Consider enhanced security presence and operational adjustments.")
    elif change_pct > 10:
        future_why.append(f"Forecast indicates <b>moderate increase</b> ({change_pct:+.1f}%) driven by continuation of recent trends and approaching peak seasonal period.")
        future_why.append("Proactive measures recommended to <b>prevent escalation</b>: increased patrols during peak hours, improved lighting, and enhanced monitoring.")
    elif change_pct < -20:
        future_why.append(f"Model projects <b>substantial improvement</b> ({change_pct:+.1f}%), likely due to mean reversion after recent spike and entering lower-risk seasonal period.")
        future_why.append("While positive, <b>maintain vigilance</b> - this improvement reflects statistical normalization rather than solved root causes.")
    elif change_pct < -10:
        future_why.append(f"Forecast suggests <b>modest improvement</b> ({change_pct:+.1f}%) as recent elevated levels stabilize and seasonal factors become more favorable.")
        future_why.append("Continue current protocols while <b>monitoring closely</b> to ensure sustained improvement.")
    else:
        future_why.append(f"Incident levels expected to <b>remain stable</b> ({change_pct:+.1f}% change) based on established patterns and seasonal consistency.")
        future_why.append("Maintain existing security measures and <b>standard operating procedures</b>.")

    next_quarter_forecast = result['forecast_values'][:3].mean()
    if next_quarter_forecast > hist_avg * 1.2:
        future_why.append(f"Next quarter average ({next_quarter_forecast:.1f}) will likely <b>exceed historical norms</b> ({hist_avg:.1f}), requiring resource reallocation and heightened awareness.")

    # Model confidence
    if result['mape'] < 15:
        future_why.append(f"High model confidence (MAPE: {result['mape']:.1f}%) indicates these predictions are <b>statistically reliable</b> for planning purposes.")
    else:
        future_why.append(f"Moderate prediction uncertainty (MAPE: {result['mape']:.1f}%) suggests treating forecasts as <b>general guidance</b> rather than precise targets.")

    return {
        'current_why': ' '.join(current_why),
        'future_why': ' '.join(future_why),
        'metrics': {
            'historical_avg': hist_avg,
            'forecast_avg': fcst_avg,
            'change_pct': change_pct,
            'recent_trend_pct': recent_trend,
            'peak_month': month_names[peak_month],
            'low_month': month_names[low_month],
        }
    }


def create_comparison_plot(
    location_result: dict,
    system_result: dict,
    location_name: str = "This Location"
) -> io.BytesIO:
    """
    Create side-by-side comparison of location vs system-wide forecast.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.patch.set_facecolor('white')

    for idx, (result, title) in enumerate([
        (location_result, location_name),
        (system_result, "CTA System-Wide")
    ]):
        ax = axes[idx]
        ax.set_facecolor('#f8f9fa')

        historical = result['historical']
        forecast_dates = result['forecast_dates']
        forecast_values = result['forecast_values']

        # Plot
        ax.plot(historical.index, historical.values,
               'o-', color=COLORS['primary'], linewidth=2, markersize=5,
               label='Historical')
        ax.plot(forecast_dates, forecast_values,
               '^--', color=COLORS['forecast'], linewidth=2.5, markersize=6,
               label='Forecast')
        ax.fill_between(forecast_dates,
                         result['forecast_lower'],
                         result['forecast_upper'],
                         alpha=0.2, color=COLORS['confidence'])

        ax.axvline(x=historical.index[-1], color='gray', linestyle=':', linewidth=2, alpha=0.5)

        # Metrics
        hist_avg = historical.mean()
        fcst_avg = forecast_values.mean()
        change = ((fcst_avg - hist_avg) / hist_avg) * 100

        metrics_text = f"Avg: {hist_avg:.1f} → {fcst_avg:.1f}\nChange: {change:+.1f}%\nMAPE: {result['mape']:.1f}%"
        ax.text(0.02, 0.98, metrics_text, transform=ax.transAxes,
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round,pad=0.6', facecolor='white', alpha=0.9),
               family='monospace')

        ax.set_title(title, fontsize=13, fontweight='bold', color='#0b2c67')
        ax.set_xlabel('Date', fontsize=10, fontweight='bold')
        ax.set_ylabel('Monthly Incidents', fontsize=10, fontweight='bold')
        ax.legend(fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close()

    return buf
