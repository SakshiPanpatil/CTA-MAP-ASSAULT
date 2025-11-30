"""
PDF Report Generator - PROFESSIONAL VERSION
Better fonts, spacing, and formatting for business presentation.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Any
from collections import Counter

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from . import ai_insights, report_analytics, forecast_analytics

# Setup logger
logger = logging.getLogger(__name__)


class ComprehensiveSafetyReport:
    """Generate comprehensive AI-powered PDF safety reports."""

    # CTA MILITARY CODE SYSTEM - Risk Assessment Matrix Colors
    CTA_BLUE = colors.HexColor("#0c5ed7")
    CTA_DARK = colors.HexColor("#0b2c67")
    DANGER = colors.HexColor("#DC143C")      # Red (Unacceptable - Critical)
    WARNING = colors.HexColor("#FF8C00")     # Orange (Undesirable)
    SUCCESS = colors.HexColor("#228B22")     # Green (Acceptable)
    YELLOW = colors.HexColor("#FFD700")      # Yellow (Accept w/ Review)
    MUTED = colors.HexColor("#5f6b7b")
    LIGHT_BG = colors.HexColor("#f8f9fa")

    def __init__(self):
        """Initialize PDF generator."""
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create professional paragraph styles."""
        if hasattr(self, '_styles_initialized'):
            return

        # Title - Large and bold
        self.styles.add(ParagraphStyle(
            name="CTAReportTitle", parent=self.styles["Heading1"],
            fontSize=26, textColor=self.CTA_DARK, spaceAfter=10,
            fontName="Helvetica-Bold", alignment=1, leading=32
        ))

        # Subtitle - Clear and readable
        self.styles.add(ParagraphStyle(
            name="CTAReportSubtitle", parent=self.styles["Normal"],
            fontSize=13, textColor=self.CTA_BLUE, spaceAfter=16,
            fontName="Helvetica", alignment=1, leading=18
        ))

        # Section Header - Professional
        self.styles.add(ParagraphStyle(
            name="CTASectionHeader", parent=self.styles["Heading1"],
            fontSize=16, textColor=self.CTA_BLUE, spaceAfter=10,
            spaceBefore=16, fontName="Helvetica-Bold", leading=20
        ))

        # Subsection - Clear hierarchy
        self.styles.add(ParagraphStyle(
            name="CTASubsection", parent=self.styles["Heading2"],
            fontSize=13, textColor=self.CTA_DARK, spaceAfter=8,
            spaceBefore=10, fontName="Helvetica-Bold", leading=16
        ))

        # Body Text - Readable and professional
        self.styles.add(ParagraphStyle(
            name="CTABodyText", parent=self.styles["Normal"],
            fontSize=10, textColor=colors.black, spaceAfter=8,
            leading=15, alignment=4  # Justify
        ))

        # Highlight Box - Emphasis areas
        self.styles.add(ParagraphStyle(
            name="CTAHighlightBox", parent=self.styles["Normal"],
            fontSize=10, textColor=self.CTA_DARK, fontName="Helvetica",
            spaceAfter=12, leading=15, leftIndent=15, rightIndent=15,
            backColor=self.LIGHT_BG, borderPadding=12
        ))

        # Plot Summary - Smaller italic
        self.styles.add(ParagraphStyle(
            name="CTAPlotSummary", parent=self.styles["Normal"],
            fontSize=9, textColor=self.MUTED, spaceAfter=8,
            leading=13, leftIndent=10, rightIndent=10, fontName="Helvetica-Oblique"
        ))

        # Metric value style - clear, centered numbers/text
        self.styles.add(ParagraphStyle(
            name="CTAMetricValue", parent=self.styles["Normal"],
            fontSize=13, textColor=colors.black, spaceAfter=0,
            leading=15, alignment=1, fontName="Helvetica-Bold"
        ))

        self._styles_initialized = True

    def _safe_text(self, text: str, max_len: int = 1500) -> str:
        """Safely truncate and convert markdown to HTML."""
        if not text:
            return ""
        text = str(text).strip()

        # If text exceeds limit, truncate smartly at sentence boundary
        if len(text) > max_len:
            # Try to find last sentence end before max_len
            truncated = text[:max_len]

            # Look for sentence endings (., !, ?) within last 100 chars
            for delimiter in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                last_sentence = truncated.rfind(delimiter)
                if last_sentence > max_len - 200:  # Found a sentence end near the limit
                    text = text[:last_sentence + 1]
                    break
            else:
                # No sentence boundary found, try word boundary
                last_space = truncated.rfind(' ')
                if last_space > 0:
                    text = text[:last_space] + "..."
                else:
                    text = truncated + "..."

        return ai_insights.markdown_to_html(text)

    def _p(self, text: str) -> Paragraph:
        """Shortcut to wrap text in a body paragraph for consistent wrapping."""
        return Paragraph(str(text), self.styles["CTABodyText"])

    def _add_cover_page(self, story: list, title: str, subtitle: str, context_info: dict = None):
        """Add professional cover page with specific details."""
        story.append(Spacer(1, 1.5 * inch))
        story.append(Paragraph("CTA SAFETY & SECURITY ANALYSIS", self.styles["CTAReportSubtitle"]))
        story.append(Spacer(1, 0.4 * inch))
        story.append(Paragraph(title, self.styles["CTAReportTitle"]))
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph(subtitle, self.styles["CTAReportSubtitle"]))
        story.append(Spacer(1, 1.2 * inch))

        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        meta_data = [
            ["Report Generated:", timestamp],
            ["Classification:", "Confidential - Internal Use"],
            ["Department:", "CTA Safety & Security Division"],
        ]

        # Add specific context if provided
        if context_info:
            for key, value in context_info.items():
                meta_data.append([key, str(value)])

        meta_table = Table(meta_data, colWidths=[2.2 * inch, 3.8 * inch])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), self.CTA_BLUE),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
            ("BACKGROUND", (1, 0), (1, -1), self.LIGHT_BG),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 15),
            ("GRID", (0, 0), (-1, -1), 1.5, colors.white),
        ]))
        story.append(meta_table)
        story.append(PageBreak())

    def _add_metrics_grid(self, story: list, metrics: list[tuple[str, str, colors.Color]]):
        """Add professional metrics grid with wrapped values for long text."""
        rows = []
        current_row = []
        for i, (label, value, color) in enumerate(metrics):
            # Wrap long values (e.g., date ranges) so they don't overflow the cell
            label_cell = Paragraph(f"<b>{label}</b>", self.styles["CTABodyText"])
            value_text = str(value)
            value_cell = Paragraph(value_text, self.styles["CTAMetricValue"])

            data = [[label_cell], [value_cell]]
            table = Table(data, colWidths=[2.3 * inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 2, colors.white),
            ]))
            current_row.append(table)
            if len(current_row) == 3 or i == len(metrics) - 1:
                while len(current_row) < 3:
                    current_row.append(Spacer(2.3 * inch, 0))
                rows.append(current_row)
                current_row = []

        grid_table = Table(rows, colWidths=[2.3 * inch] * 3, hAlign="LEFT", spaceBefore=6, spaceAfter=6)
        story.append(grid_table)
        story.append(Spacer(1, 0.2 * inch))

    def _add_plot_with_summary(self, story: list, plot_image: io.BytesIO, plot_type: str,
                              data_summary: dict[str, Any], width: float = 6, height: float = 2.6):
        """Add plot with AI-generated summary."""
        # Generate AI summary
        summary = ai_insights.generate_plot_summary(plot_type, data_summary)
        summary_html = ai_insights.markdown_to_html(summary)

        # Add plot
        story.append(Image(plot_image, width=width*inch, height=height*inch))
        story.append(Spacer(1, 0.03*inch))
        # Add summary
        story.append(Paragraph(f"<i>{summary_html}</i>", self.styles["CTAPlotSummary"]))
        story.append(Spacer(1, 0.1*inch))

    def _add_all_incidents_detailed(self, story: list, incidents: list[dict[str, Any]]):
        """Add ALL incidents with proper spacing."""
        story.append(Paragraph(f"Complete Incident Records ({len(incidents)} Total)", self.styles["CTASectionHeader"]))
        story.append(Paragraph(
            "Comprehensive listing of all safety incidents with complete details from the database.",
            self.styles["CTABodyText"]
        ))
        story.append(Spacer(1, 0.1 * inch))

        for idx, inc in enumerate(incidents, 1):
            incident_data = []

            # Header row - MORE SPECIFIC - CTA MATRIX COLORS
            event_type = self._safe_text(inc.get("event_type") or "Unknown Event", 60)
            event_type_group = inc.get("event_type_group", "")
            severity = inc.get("severity_score", 1)
            # CTA Risk Matrix color mapping
            if severity >= 5:
                sev_color = self.DANGER      # Red (Critical)
            elif severity >= 4:
                sev_color = self.WARNING     # Orange (High)
            elif severity >= 3:
                sev_color = self.YELLOW      # Yellow (Medium)
            elif severity >= 2:
                sev_color = colors.HexColor("#9ACD32")  # Yellow-Green
            else:
                sev_color = self.SUCCESS     # Green (Low)

            # Include incident number if available
            inc_number = inc.get("incident_number", f"INC-{idx:04d}")

            incident_data.append([
                self._p(f"<b>#{idx}</b><br/><font size=7>{inc_number}</font>"),
                self._p(f"<b>{event_type}</b>"),
                self._p(f"<b>Severity {severity}/5</b><br/><font size=7>{event_type_group or 'N/A'}</font>"),
            ])

            # Date & Time - MORE COMPLETE
            date_val = self._safe_text(inc.get("event_date") or "N/A", 30)
            time_val = self._safe_text(inc.get("event_time") or "N/A", 25)
            incident_data.append([
                self._p("<b>Date/Time:</b>"),
                self._p(f"{date_val} at {time_val}"),
                self._p(f"Year: {inc.get('year', 'N/A')}")
            ])

            # Location - COMPLETE ADDRESS DETAILS
            location = self._safe_text(inc.get("approximate_address") or inc.get("location_type") or "N/A", 90)
            lat = inc.get("latitude", "N/A")
            lon = inc.get("longitude", "N/A")
            incident_data.append([
                self._p("<b>Location:</b>"),
                self._p(f"{location}<br/><font size=7>Lat: {lat}, Lon: {lon}</font>"),
                ""
            ])

            # Injuries - COMPLETE BREAKDOWN
            total_inj = inc.get("total_injuries", 0) or 0
            op_inj = inc.get("transit_vehicle_operator_injuries", 0) or 0
            rider_inj = inc.get("transit_vehicle_rider_injuries", 0) or 0
            incident_data.append([
                self._p("<b>Injuries:</b>"),
                self._p(f"Total: {total_inj} (Op: {op_inj}, Rider: {rider_inj})"),
                self._p(f"Other: {inc.get('other_injuries', 0) or 0}")
            ])

            # Vehicle & Route info if available
            vehicle = inc.get("vehicle_number", "")
            route = inc.get("route_id", "")
            if vehicle or route:
                incident_data.append([
                    self._p("<b>Vehicle/Route:</b>"),
                    self._p(f"Vehicle: {vehicle or 'N/A'}"),
                    self._p(f"Route: {route or 'N/A'}")
                ])

            # Description - FULL DETAILS
            desc = inc.get("description", "")
            if desc and str(desc).strip():
                desc_text = self._safe_text(desc, 800)  # Allow more description before truncation
                incident_data.append([
                    self._p("<b>Incident Details:</b>"),
                    Paragraph(desc_text, self.styles["CTABodyText"]),
                    ""
                ])

            # Create table - COMPACT
            inc_table = Table(incident_data, colWidths=[0.8 * inch, 3.6 * inch, 2.1 * inch])
            inc_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), sev_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (0, -1), self.LIGHT_BG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
            ]))

            story.append(inc_table)
            story.append(Spacer(1, 0.06 * inch))  # ULTRA MINIMAL gap

    def generate_stop_report(self, stop_name: str, stop_lat: float, stop_lon: float,
                            radius_km: float, all_assaults: list[dict[str, Any]]) -> bytes:
        """Generate comprehensive stop safety report."""
        logger.info("="*80)
        logger.info(f"STOP REPORT - Generating for: {stop_name}")
        logger.info(f"   Location: ({stop_lat:.4f}, {stop_lon:.4f}), Radius: {radius_km}km")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
        story = []

        # Filter & analyze FIRST to get count
        logger.info(f"Filtering incidents within {radius_km}km radius...")
        nearby = report_analytics.filter_assaults_by_radius(all_assaults, stop_lat, stop_lon, radius_km)
        logger.info(f"   Found {len(nearby)} incidents nearby")

        # Cover - SPECIFIC TITLE
        specific_title = f"Stop Safety Analysis: {stop_name}"
        specific_subtitle = f"{len(nearby)} Assault Incidents within {radius_km}km Radius"
        context_info = {
            "Stop Location": stop_name,
            "Coordinates": f"Lat {stop_lat:.4f}, Lon {stop_lon:.4f}",
            "Analysis Radius": f"{radius_km} kilometers",
            "Total Incidents": str(len(nearby)),
        }
        self._add_cover_page(story, specific_title, specific_subtitle, context_info)
        metrics = report_analytics.calculate_stop_safety_metrics(nearby)
        date_range = report_analytics.get_date_range(nearby)

        # Metrics
        risk_color = self.SUCCESS if metrics["risk_level"] == "LOW" else self.WARNING if metrics["risk_level"] == "MODERATE" else self.DANGER
        metrics_data = [
            ("Total Incidents", str(len(nearby)), risk_color),
            ("Total Injuries", str(metrics["total_injuries"]), self.DANGER),
            ("Safety Score", f"{metrics['safety_score']}/100", risk_color),
            ("Risk Level", metrics["risk_level"], risk_color),
            ("Date Range", date_range, self.MUTED),
            ("Analysis Radius", f"{radius_km} km", self.CTA_BLUE),
        ]
        self._add_metrics_grid(story, metrics_data)

        if not nearby:
            # No incidents case
            story.append(Paragraph("Executive Summary", self.styles["CTASectionHeader"]))
            story.append(Paragraph(
                f"<b>No incidents recorded within {radius_km}km of this location.</b> This indicates a low-risk area. Continue standard safety monitoring protocols.",
                self.styles["CTAHighlightBox"]
            ))
        else:
            # UNIFIED AI CALL - Generate ALL insights in ONE shot (8x-9x faster!)
            logger.info("Preparing data for unified AI analysis...")
            # Prepare all data first
            dates = [report_analytics.parse_assault_date(a.get("event_date")) for a in nearby]
            dates = [d for d in dates if d is not None]
            date_counts = Counter([d.strftime("%Y-%m") for d in dates]) if dates else {}

            hours = [report_analytics.parse_time(a.get("event_time")) for a in nearby]
            hours = [h for h in hours if h is not None]
            hour_counts = Counter(hours) if hours else {}

            event_types = [a.get("event_type") for a in nearby if a.get("event_type")]
            type_counts = Counter(event_types) if event_types else Counter()

            severities = [a.get("severity_score", 1) for a in nearby]
            sev_counts = Counter(severities) if severities else {}

            logger.info("Calling unified AI insights generator...")
            # Single unified LLM call for ALL text insights
            all_insights = ai_insights.generate_complete_report_insights(
                total_incidents=len(nearby),
                total_injuries=metrics["total_injuries"],
                date_range=date_range,
                location_context=f"{stop_name} within {radius_km}km",
                severity_breakdown={f"Level {i}": len([a for a in nearby if a.get("severity_score") == i]) for i in range(1, 6)},
                incident_summaries=[{"date": a.get("event_date"), "type": a.get("event_type"),
                                   "severity": a.get("severity_score"), "injuries": a.get("total_injuries")} for a in nearby[:20]],
                temporal_patterns={"total": len(nearby), "date_range": date_range},
                plot_summaries_data={
                    "timeline": {"monthly_counts": dict(date_counts), "total": len(nearby)},
                    "hourly": {"hourly_distribution": dict(hour_counts),
                              "peak_hours": sorted(hour_counts, key=hour_counts.get, reverse=True)[:3] if hour_counts else []},
                    "event_types": {"type_distribution": dict(type_counts.most_common(5)), "total_types": len(type_counts)},
                    "severity": {"severity_distribution": dict(sev_counts),
                                "avg_severity": sum(severities)/len(severities) if severities else 0}
                },
                risk_level=metrics["risk_level"],
                key_findings=metrics
            )
            logger.info("AI insights received; building PDF sections...")

            # Executive Summary (using unified insights)
            logger.info("   Adding Executive Summary section...")
            story.append(Paragraph("Executive Summary", self.styles["CTASectionHeader"]))
            story.append(Paragraph(self._safe_text(all_insights.get("executive_summary", ""), 1500),
                                 self.styles["CTAHighlightBox"]))
            story.append(Spacer(1, 0.15 * inch))

            # Temporal Analysis
            logger.info("   Generating plots and temporal analysis...")
            story.append(Paragraph("Temporal Analysis", self.styles["CTASectionHeader"]))

            # Timeline with AI summary
            time_series = report_analytics.create_time_series_plot(nearby)
            story.append(Image(time_series, width=6.2*inch, height=2.5*inch))
            story.append(Spacer(1, 0.03*inch))
            story.append(Paragraph(f"<i>{ai_insights.markdown_to_html(all_insights.get('plot_summary_timeline', ''))}</i>",
                                 self.styles["CTAPlotSummary"]))
            story.append(Spacer(1, 0.1*inch))

            # Hourly with AI summary
            hourly = report_analytics.create_hourly_pattern(nearby)
            story.append(Image(hourly, width=6.2*inch, height=2.8*inch))
            story.append(Spacer(1, 0.03*inch))
            story.append(Paragraph(f"<i>{ai_insights.markdown_to_html(all_insights.get('plot_summary_hourly', ''))}</i>",
                                 self.styles["CTAPlotSummary"]))
            story.append(Spacer(1, 0.1*inch))

            # Classification
            story.append(Paragraph("Incident Classification", self.styles["CTASectionHeader"]))

            # Event types with AI summary
            event_breakdown = report_analytics.create_event_type_breakdown(nearby)
            story.append(Image(event_breakdown, width=5.5*inch, height=4*inch))
            story.append(Spacer(1, 0.03*inch))
            story.append(Paragraph(f"<i>{ai_insights.markdown_to_html(all_insights.get('plot_summary_event_types', ''))}</i>",
                                 self.styles["CTAPlotSummary"]))
            story.append(Spacer(1, 0.1*inch))

            # Severity with AI summary
            severity_dist = report_analytics.create_severity_distribution(nearby)
            story.append(Image(severity_dist, width=5.5*inch, height=3.2*inch))
            story.append(Spacer(1, 0.03*inch))
            story.append(Paragraph(f"<i>{ai_insights.markdown_to_html(all_insights.get('plot_summary_severity', ''))}</i>",
                                 self.styles["CTAPlotSummary"]))
            story.append(Spacer(1, 0.1*inch))

            # NEW: Predictive Analytics Section
            logger.info("   🔮 Adding Predictive Analytics section...")
            story.append(PageBreak())
            story.append(Paragraph("Predictive Analytics & Future Trends", self.styles["CTASectionHeader"]))
            story.append(Paragraph(
                "Machine learning-based forecast using SARIMAX time series model. "
                "Predictions based on historical patterns, seasonal trends, and statistical modeling.",
                self.styles["CTABodyText"]
            ))
            story.append(Spacer(1, 0.1*inch))

            # Prepare time series data for forecasting
            monthly_series, ts_metadata = forecast_analytics.prepare_time_series_data(nearby)

            if monthly_series is not None and len(monthly_series) >= 12:
                # Train forecast model
                forecast_result = forecast_analytics.train_sarimax_forecast(monthly_series, forecast_periods=6)

                if forecast_result:
                    # Seasonal Decomposition
                    story.append(Paragraph("Seasonal Pattern Analysis", self.styles["CTASubsection"]))
                    decomp_plot = forecast_analytics.create_seasonal_decomposition_plot(monthly_series, stop_name)
                    if decomp_plot:
                        story.append(Image(decomp_plot, width=6.2*inch, height=4.2*inch))
                        story.append(Spacer(1, 0.03*inch))
                        story.append(Paragraph(
                            f"<i>Decomposition reveals underlying patterns: trend direction, seasonal cycles (peak: {ts_metadata.get('max_monthly', 0):.0f}/month, "
                            f"low: {ts_metadata.get('min_monthly', 0):.0f}/month), and random variations. "
                            f"Understanding these components improves forecast accuracy.</i>",
                            self.styles["CTAPlotSummary"]
                        ))
                        story.append(Spacer(1, 0.15*inch))

                    # 6-Month Forecast with Metrics
                    story.append(Paragraph("6-Month Predictive Forecast", self.styles["CTASubsection"]))
                    forecast_plot = forecast_analytics.create_enhanced_forecast_plot(
                        forecast_result,
                        title=stop_name,
                        show_metrics=True
                    )
                    story.append(Image(forecast_plot, width=6.5*inch, height=3.2*inch))
                    story.append(Spacer(1, 0.03*inch))

                    # Forecast summary with metrics
                    fcst_avg = forecast_result['forecast_values'].mean()
                    hist_avg = ts_metadata['avg_monthly']
                    change_pct = ((fcst_avg - hist_avg) / hist_avg) * 100
                    change_color = "red" if change_pct > 10 else "green" if change_pct < -10 else "orange"

                    story.append(Paragraph(
                        f"<i><b>Model Performance:</b> MAE {forecast_result['mae']:.2f}, RMSE {forecast_result['rmse']:.2f}, MAPE {forecast_result['mape']:.1f}% | "
                        f"<b>Forecast:</b> Expected {fcst_avg:.1f} incidents/month (next 6 months), "
                        f"<font color='{change_color}'>{change_pct:+.1f}% change</font> from historical average ({hist_avg:.1f}/month).</i>",
                        self.styles["CTAPlotSummary"]
                    ))
                    story.append(Spacer(1, 0.15*inch))

                    # WHY Analysis - Most Important Part
                    why_analysis = forecast_analytics.generate_why_analysis(forecast_result, monthly_series, stop_name)

                    story.append(Paragraph("Understanding Current Trends - WHY NOW?", self.styles["CTASubsection"]))
                    story.append(Paragraph(
                        why_analysis['current_why'],
                        self.styles["CTAHighlightBox"]
                    ))
                    story.append(Spacer(1, 0.1*inch))

                    story.append(Paragraph("Future Trend Projection - WHY NEXT?", self.styles["CTASubsection"]))
                    story.append(Paragraph(
                        why_analysis['future_why'],
                        self.styles["CTAHighlightBox"]
                    ))
                    story.append(Spacer(1, 0.15*inch))

                    # Key Metrics Summary Box
                    story.append(Paragraph("Forecast Summary & Risk Assessment", self.styles["CTASubsection"]))
                    metrics_summary = [
                        ["Metric", "Historical", "Forecast", "Change"],
                        [
                            "Monthly Average",
                            f"{hist_avg:.1f}",
                            f"{fcst_avg:.1f}",
                            f"{change_pct:+.1f}%"
                        ],
                        [
                            "Next Quarter Total",
                            f"{hist_avg * 3:.0f}",
                            f"{forecast_result['forecast_values'][:3].sum():.0f}",
                            ""
                        ],
                        [
                            "Peak Season",
                            why_analysis['metrics']['peak_month'],
                            why_analysis['metrics']['peak_month'],
                            "Seasonal"
                        ],
                        [
                            "Model Confidence",
                            f"MAPE: {forecast_result['mape']:.1f}%",
                            "80% CI shown",
                            "High" if forecast_result['mape'] < 15 else "Moderate"
                        ]
                    ]

                    metrics_table = Table(metrics_summary, colWidths=[2.2*inch, 1.5*inch, 1.5*inch, 1.3*inch])
                    metrics_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), self.CTA_BLUE),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]))
                    story.append(metrics_table)

                else:
                    story.append(Paragraph(
                        f"<i>Model training failed. This can occur with irregular patterns or insufficient data quality. "
                        f"Current: {ts_metadata.get('total_months', 0)} months. Consider collecting more consistent historical data.</i>",
                        self.styles["CTAPlotSummary"]
                    ))
            else:
                story.append(Paragraph(
                    "<i>Predictive modeling unavailable: Requires minimum 12 months of historical data. "
                    f"Current dataset: {ts_metadata.get('total_months', 0) if ts_metadata else 0} months. "
                    "Continue collecting data to enable future trend analysis.</i>",
                    self.styles["CTAPlotSummary"]
                ))

            story.append(PageBreak())

            # AI Insights
            story.append(Paragraph("AI-Powered Insights", self.styles["CTASectionHeader"]))
            story.append(Paragraph(self._safe_text(all_insights.get("pattern_analysis", ""), 3500),
                                 self.styles["CTABodyText"]))

            # Recommendations
            story.append(Paragraph("Recommendations", self.styles["CTASectionHeader"]))
            story.append(Paragraph(self._safe_text(all_insights.get("recommendations", ""), 4000),
                                 self.styles["CTABodyText"]))

            story.append(PageBreak())

            # Complete incident listing
            logger.info("   Adding complete incident listings...")
            self._add_all_incidents_detailed(story, nearby)

        logger.info("Building final PDF document...")
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        logger.info(f"STOP REPORT COMPLETE - PDF size: {len(pdf_bytes)} bytes")
        logger.info("="*80)
        return pdf_bytes

    def generate_assault_cluster_report(self, assaults: list[dict[str, Any]]) -> bytes:
        """Generate assault cluster report."""
        logger.info("="*80)
        logger.info(f"CLUSTER REPORT - Generating for {len(assaults)} incidents")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
        story = []

        # Calculate metrics FIRST
        total = len(assaults)

        # Get location info from first few incidents
        locations = [a.get("approximate_address", "") for a in assaults[:5] if a.get("approximate_address")]
        primary_location = locations[0] if locations else "CTA Transit System"

        # Cover - SPECIFIC TITLE
        specific_title = f"Assault Cluster Investigation Report"
        specific_subtitle = f"{total} Related Incidents - {primary_location}"

        # Calculate date range for context
        dates = [report_analytics.parse_assault_date(a.get("event_date")) for a in assaults]
        dates = [d for d in dates if d is not None]
        if dates:
            min_date = min(dates).strftime("%B %Y")
            max_date = max(dates).strftime("%B %Y")
            date_span = f"{min_date} to {max_date}"
        else:
            date_span = "Date range unavailable"

        context_info = {
            "Incident Count": f"{total} assault incidents",
            "Time Period": date_span,
            "Primary Location": primary_location[:50],
            "Analysis Type": "Clustered Incident Investigation",
        }
        self._add_cover_page(story, specific_title, specific_subtitle, context_info)
        total_injuries = sum(int(a.get("total_injuries", 0) or 0) for a in assaults)
        operator_inj = sum(int(a.get("transit_vehicle_operator_injuries", 0) or 0) for a in assaults)
        rider_inj = sum(int(a.get("transit_vehicle_rider_injuries", 0) or 0) for a in assaults)
        avg_sev = sum(int(a.get("severity_score", 1) or 1) for a in assaults) / total if total > 0 else 0
        date_range = report_analytics.get_date_range(assaults)
        safety_score = max(0, 100 - (total * 5) - (avg_sev * 3) - (total_injuries * 2))
        risk_level = "HIGH" if safety_score < 40 else "MODERATE" if safety_score < 70 else "LOW"

        # Metrics
        metrics_data = [
            ("Total Incidents", str(total), self.DANGER),
            ("Total Injuries", str(total_injuries), self.DANGER),
            ("Operator Injuries", str(operator_inj), self.WARNING),
            ("Rider Injuries", str(rider_inj), self.WARNING),
            ("Average Severity", f"{avg_sev:.1f}/5", self.CTA_BLUE),
            ("Date Range", date_range, self.MUTED),
        ]
        self._add_metrics_grid(story, metrics_data)

        # UNIFIED AI CALL - Prepare all data
        logger.info("Preparing cluster data for unified AI analysis...")
        dates = [report_analytics.parse_assault_date(a.get("event_date")) for a in assaults]
        dates = [d for d in dates if d is not None]
        date_counts = Counter([d.strftime("%Y-%m") for d in dates]) if dates else {}

        hours = [report_analytics.parse_time(a.get("event_time")) for a in assaults]
        hours = [h for h in hours if h is not None]
        hour_counts = Counter(hours) if hours else Counter()

        event_types = [a.get("event_type") for a in assaults if a.get("event_type")]
        type_counts = Counter(event_types) if event_types else Counter()

        severities = [a.get("severity_score", 1) for a in assaults]
        sev_counts = Counter(severities) if severities else {}

        logger.info("Calling unified AI insights generator for cluster...")
        # Single unified LLM call for ALL text insights
        all_insights = ai_insights.generate_complete_report_insights(
            total_incidents=total,
            total_injuries=total_injuries,
            date_range=date_range,
            location_context="CTA transit cluster zone",
            severity_breakdown={f"Level {i}": len([a for a in assaults if a.get("severity_score") == i]) for i in range(1, 6)},
            incident_summaries=[{"date": a.get("event_date"), "type": a.get("event_type"),
                               "severity": a.get("severity_score"), "injuries": a.get("total_injuries"),
                               "description": str(a.get("description", ""))[:80]} for a in assaults[:20]],
            temporal_patterns={"total": total, "date_range": date_range},
            plot_summaries_data={
                "timeline": {"monthly_counts": dict(date_counts), "total": total},
                "hourly": {"hourly_distribution": dict(hour_counts),
                          "peak_hours": sorted(hour_counts, key=hour_counts.get, reverse=True)[:3] if hour_counts else []},
                "event_types": {"type_distribution": dict(type_counts.most_common(5)), "total_types": len(type_counts)},
                "severity": {"severity_distribution": dict(sev_counts), "avg_severity": avg_sev}
            },
            risk_level=risk_level,
            key_findings={"incidents": total, "injuries": total_injuries, "risk": risk_level}
        )
        logger.info("AI insights received; building cluster PDF sections...")

        # Executive Summary
        logger.info("   📝 Adding Executive Summary...")
        story.append(Paragraph("Executive Summary", self.styles["CTASectionHeader"]))
        story.append(Paragraph(self._safe_text(all_insights.get("executive_summary", ""), 1500),
                             self.styles["CTAHighlightBox"]))
        story.append(Spacer(1, 0.15*inch))

        # Temporal Patterns
        logger.info("   Generating cluster plots...")
        story.append(Paragraph("Temporal Patterns", self.styles["CTASectionHeader"]))

        time_series = report_analytics.create_time_series_plot(assaults)
        story.append(Image(time_series, width=6.2*inch, height=2.5*inch))
        story.append(Spacer(1, 0.03*inch))
        story.append(Paragraph(f"<i>{ai_insights.markdown_to_html(all_insights.get('plot_summary_timeline', ''))}</i>",
                             self.styles["CTAPlotSummary"]))
        story.append(Spacer(1, 0.1*inch))

        hourly = report_analytics.create_hourly_pattern(assaults)
        story.append(Image(hourly, width=6.2*inch, height=2.8*inch))
        story.append(Spacer(1, 0.03*inch))
        story.append(Paragraph(f"<i>{ai_insights.markdown_to_html(all_insights.get('plot_summary_hourly', ''))}</i>",
                             self.styles["CTAPlotSummary"]))
        story.append(Spacer(1, 0.1*inch))

        story.append(PageBreak())

        # Classification
        story.append(Paragraph("Incident Classification", self.styles["CTASectionHeader"]))

        event_breakdown = report_analytics.create_event_type_breakdown(assaults)
        story.append(Image(event_breakdown, width=5.5*inch, height=4*inch))
        story.append(Spacer(1, 0.03*inch))
        story.append(Paragraph(f"<i>{ai_insights.markdown_to_html(all_insights.get('plot_summary_event_types', ''))}</i>",
                             self.styles["CTAPlotSummary"]))
        story.append(Spacer(1, 0.1*inch))

        severity_dist = report_analytics.create_severity_distribution(assaults)
        story.append(Image(severity_dist, width=5.5*inch, height=3.2*inch))
        story.append(Spacer(1, 0.03*inch))
        story.append(Paragraph(f"<i>{ai_insights.markdown_to_html(all_insights.get('plot_summary_severity', ''))}</i>",
                             self.styles["CTAPlotSummary"]))
        story.append(Spacer(1, 0.1*inch))

        story.append(PageBreak())

        # NEW: Predictive Analytics Section for Cluster
        logger.info("   🔮 Adding Predictive Analytics section to cluster report...")
        story.append(Paragraph("Predictive Analytics & Future Trends", self.styles["CTASectionHeader"]))
        story.append(Paragraph(
            "Machine learning-based forecast using SARIMAX time series model (Best Performer: MAE 3.14, MAPE 11.6%). "
            "Predictions based on historical patterns, seasonal trends, and statistical modeling.",
            self.styles["CTABodyText"]
        ))
        story.append(Spacer(1, 0.1*inch))

        # Prepare time series data for forecasting
        monthly_series, ts_metadata = forecast_analytics.prepare_time_series_data(assaults)

        if monthly_series is not None and len(monthly_series) >= 12:
            # Train forecast model
            forecast_result = forecast_analytics.train_sarimax_forecast(monthly_series, forecast_periods=6)

            if forecast_result:
                # Seasonal Decomposition
                story.append(Paragraph("Seasonal Pattern Analysis", self.styles["CTASubsection"]))
                decomp_plot = forecast_analytics.create_seasonal_decomposition_plot(monthly_series, "Assault Cluster")
                if decomp_plot:
                    story.append(Image(decomp_plot, width=6.2*inch, height=4.2*inch))
                    story.append(Spacer(1, 0.03*inch))
                    story.append(Paragraph(
                        f"<i>Decomposition reveals underlying patterns: trend direction, seasonal cycles (peak: {ts_metadata.get('max_monthly', 0):.0f}/month, "
                        f"low: {ts_metadata.get('min_monthly', 0):.0f}/month), and random variations. "
                        f"Understanding these components improves forecast accuracy.</i>",
                        self.styles["CTAPlotSummary"]
                    ))
                    story.append(Spacer(1, 0.15*inch))

                # 6-Month Forecast with Metrics
                story.append(Paragraph("6-Month Predictive Forecast", self.styles["CTASubsection"]))
                forecast_plot = forecast_analytics.create_enhanced_forecast_plot(
                    forecast_result,
                    title="Assault Cluster Forecast",
                    show_metrics=True
                )
                story.append(Image(forecast_plot, width=6.5*inch, height=3.2*inch))
                story.append(Spacer(1, 0.03*inch))

                # Forecast summary with metrics
                fcst_avg = forecast_result['forecast_values'].mean()
                hist_avg = ts_metadata['avg_monthly']
                change_pct = ((fcst_avg - hist_avg) / hist_avg) * 100
                change_color = "red" if change_pct > 10 else "green" if change_pct < -10 else "orange"

                story.append(Paragraph(
                    f"<i><b>Model Performance:</b> MAE {forecast_result['mae']:.2f}, RMSE {forecast_result['rmse']:.2f}, MAPE {forecast_result['mape']:.1f}% | "
                    f"<b>Forecast:</b> Expected {fcst_avg:.1f} incidents/month (next 6 months), "
                    f"<font color='{change_color}'>{change_pct:+.1f}% change</font> from historical average ({hist_avg:.1f}/month).</i>",
                    self.styles["CTAPlotSummary"]
                ))
                story.append(Spacer(1, 0.15*inch))

                # WHY Analysis - Most Important Part
                why_analysis = forecast_analytics.generate_why_analysis(forecast_result, monthly_series, "Assault Cluster")

                story.append(Paragraph("Understanding Current Trends - WHY NOW?", self.styles["CTASubsection"]))
                story.append(Paragraph(
                    why_analysis['current_why'],
                    self.styles["CTAHighlightBox"]
                ))
                story.append(Spacer(1, 0.1*inch))

                story.append(Paragraph("Future Trend Projection - WHY NEXT?", self.styles["CTASubsection"]))
                story.append(Paragraph(
                    why_analysis['future_why'],
                    self.styles["CTAHighlightBox"]
                ))
                story.append(Spacer(1, 0.15*inch))

                # Key Metrics Summary Box
                story.append(Paragraph("Forecast Summary & Risk Assessment", self.styles["CTASubsection"]))
                metrics_summary = [
                    ["Metric", "Historical", "Forecast", "Change"],
                    [
                        "Monthly Average",
                        f"{hist_avg:.1f}",
                        f"{fcst_avg:.1f}",
                        f"{change_pct:+.1f}%"
                    ],
                    [
                        "Next Quarter Total",
                        f"{hist_avg * 3:.0f}",
                        f"{forecast_result['forecast_values'][:3].sum():.0f}",
                        ""
                    ],
                    [
                        "Peak Season",
                        why_analysis['metrics']['peak_month'],
                        why_analysis['metrics']['peak_month'],
                        "Seasonal"
                    ],
                    [
                        "Model Confidence",
                        f"MAPE: {forecast_result['mape']:.1f}%",
                        "80% CI shown",
                        "High" if forecast_result['mape'] < 15 else "Moderate"
                    ]
                ]

                metrics_table = Table(metrics_summary, colWidths=[2.2*inch, 1.5*inch, 1.5*inch, 1.3*inch])
                metrics_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), self.CTA_BLUE),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.LIGHT_BG]),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(metrics_table)

            else:
                story.append(Paragraph(
                    f"<i>Model training failed. This can occur with irregular patterns or insufficient data quality. "
                    f"Current: {ts_metadata.get('total_months', 0)} months. Consider collecting more consistent historical data.</i>",
                    self.styles["CTAPlotSummary"]
                ))
        else:
            story.append(Paragraph(
                "<i>Predictive modeling unavailable: Requires minimum 12 months of historical data. "
                f"Current dataset: {ts_metadata.get('total_months', 0) if ts_metadata else 0} months. "
                "Continue collecting data to enable future trend analysis.</i>",
                self.styles["CTAPlotSummary"]
            ))

        story.append(PageBreak())

        # AI Analysis
        story.append(Paragraph("AI-Powered Analysis", self.styles["CTASectionHeader"]))
        story.append(Paragraph(self._safe_text(all_insights.get("pattern_analysis", ""), 3500),
                             self.styles["CTABodyText"]))
        story.append(Spacer(1, 0.15*inch))

        # Recommendations
        story.append(Paragraph("Recommendations", self.styles["CTASectionHeader"]))
        story.append(Paragraph(self._safe_text(all_insights.get("recommendations", ""), 4000),
                             self.styles["CTABodyText"]))

        story.append(PageBreak())

        # Complete incident listing
        logger.info("   Adding complete incident listings...")
        self._add_all_incidents_detailed(story, assaults)

        logger.info("Building final cluster PDF document...")
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.read()
        logger.info(f"CLUSTER REPORT COMPLETE - PDF size: {len(pdf_bytes)} bytes")
        logger.info("="*80)
        return pdf_bytes


SafetyReportGenerator = ComprehensiveSafetyReport
