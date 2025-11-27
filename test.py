"""Quick sanity checks for date parsing and date range formatting, plus a PDF preview."""
import sys
import types
from importlib import util
from pathlib import Path

BASE = Path(__file__).parent
SERVICES_DIR = BASE / "backend" / "app" / "services"


def register_stub_packages():
    """Register lightweight package stubs so we can load services without the full app."""
    backend = types.ModuleType("backend")
    backend.__path__ = [str(BASE / "backend")]
    sys.modules.setdefault("backend", backend)

    app = types.ModuleType("backend.app")
    app.__path__ = [str(BASE / "backend" / "app")]
    sys.modules.setdefault("backend.app", app)

    services = types.ModuleType("backend.app.services")
    services.__path__ = [str(SERVICES_DIR)]
    sys.modules.setdefault("backend.app.services", services)


def load_service_module(name: str):
    """Load a service module by filename into the stub package."""
    module_path = SERVICES_DIR / f"{name}.py"
    spec = util.spec_from_file_location(f"backend.app.services.{name}", module_path)
    module = util.module_from_spec(spec)
    assert spec and spec.loader, f"Unable to load {name}"
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main():
    register_stub_packages()

    ra = load_service_module("report_analytics")
    ai_insights = load_service_module("ai_insights")
    forecast_analytics = load_service_module("forecast_analytics")
    pdf_gen = load_service_module("pdf_generator")

    sample_assaults = [
        {"event_date": "2016 September 30", "severity_score": 3, "total_injuries": 2, "latitude": 41.88, "longitude": -87.63},
        {"event_date": "September 26, 2014", "severity_score": 2, "total_injuries": 0, "latitude": 41.88, "longitude": -87.63},
        {"event_date": "03/15/2015", "severity_score": 4, "total_injuries": 1, "latitude": 41.88, "longitude": -87.63},
        {"event_date": "2015-11-01", "severity_score": 1, "total_injuries": 0, "latitude": 41.88, "longitude": -87.63},
        {"event_date": "Oct 02 2016", "severity_score": 5, "total_injuries": 3, "latitude": 41.88, "longitude": -87.63},
    ]

    parsed = [ra.parse_assault_date(a["event_date"]) for a in sample_assaults]
    parsed_strings = [d.strftime("%Y-%m-%d") if d else None for d in parsed]
    print("Parsed dates:", parsed_strings)

    date_range = ra.get_date_range(sample_assaults)
    print("Date range:", date_range)
    assert date_range == "September 26, 2014 - October 02, 2016"
    print("OK: date parsing and range formatting look good.")

    # Generate a sample PDF to visually confirm the Date Range rendering.
    generator = pdf_gen.SafetyReportGenerator()
    pdf_bytes = generator.generate_stop_report(
        stop_name="Test Stop",
        stop_lat=41.88,
        stop_lon=-87.63,
        radius_km=0.4,
        all_assaults=sample_assaults,
    )
    out_path = BASE / "date_range_check.pdf"
    out_path.write_bytes(pdf_bytes)
    print(f"PDF written to {out_path.resolve()} ({len(pdf_bytes)} bytes)")
    print("Open date_range_check.pdf and confirm the Date Range looks correct.")


if __name__ == "__main__":
    main()
