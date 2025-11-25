"""
Reports API Endpoints
Provides PDF report generation for stops and assault clusters.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from backend.app.dependencies import require_token
from backend.app.services.assaults_loader import AssaultDataLoader, get_assault_loader
from backend.app.services.pdf_generator import SafetyReportGenerator

router = APIRouter()


@router.get("/stop/{stop_id}")
def generate_stop_report(
    stop_id: str,
    stop_name: str = Query(..., description="Name of the stop"),
    stop_lat: float = Query(..., description="Latitude of the stop"),
    stop_lon: float = Query(..., description="Longitude of the stop"),
    radius_km: float = Query(0.4, ge=0.1, le=2.0, description="Analysis radius in kilometers"),
    loader: AssaultDataLoader = Depends(get_assault_loader),
    _: dict = Depends(require_token),
) -> Response:
    """
    Generate a comprehensive PDF safety report for a specific stop.

    This report includes:
    - Safety metrics and risk assessment
    - Temporal analysis of nearby incidents
    - Event type breakdown
    - Severity distribution
    - Hourly patterns
    - Actionable recommendations
    """
    # Get all assault incidents
    incidents = loader.list_incidents()
    assault_dicts = [inc.model_dump() for inc in incidents]

    # Generate PDF
    generator = SafetyReportGenerator()
    try:
        pdf_bytes = generator.generate_stop_report(
            stop_name=stop_name,
            stop_lat=stop_lat,
            stop_lon=stop_lon,
            radius_km=radius_km,
            all_assaults=assault_dicts,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate PDF report: {str(exc)}"
        ) from exc

    # Return PDF as downloadable file
    filename = f"CTA_Stop_Safety_Report_{stop_id}_{stop_name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/assault-cluster")
def generate_assault_cluster_report(
    incident_ids: list[int],
    loader: AssaultDataLoader = Depends(get_assault_loader),
    _: dict = Depends(require_token),
) -> Response:
    """
    Generate a comprehensive PDF analysis report for a cluster of assault incidents.

    This report includes:
    - Cluster statistics and injury counts
    - Temporal distribution analysis
    - Incident type breakdown
    - Injury impact analysis
    - Severity profile
    - Time-of-day patterns
    - Detailed incident records
    """
    # Get all incidents
    all_incidents = loader.list_incidents()

    # Filter to requested incidents
    incident_id_set = set(incident_ids)
    selected_incidents = [
        inc for inc in all_incidents if inc.incident_number and inc.incident_number in incident_id_set
    ]

    if not selected_incidents:
        raise HTTPException(
            status_code=404, detail="No incidents found matching the provided IDs"
        )

    # Convert to dicts
    assault_dicts = [inc.model_dump() for inc in selected_incidents]

    # Generate PDF
    generator = SafetyReportGenerator()
    try:
        pdf_bytes = generator.generate_assault_cluster_report(assault_dicts)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate PDF report: {str(exc)}"
        ) from exc

    # Return PDF
    filename = f"CTA_Assault_Cluster_Report_{len(selected_incidents)}_incidents.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
