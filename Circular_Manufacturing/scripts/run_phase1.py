from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from circular_battery.reporting.report import write_report
path = Path(__file__).resolve().parents[1] / "artifacts" / "phase1_engineering_report.json"
r = write_report(path)
print(f"PHASE1_REPORT={path}")
print(f"PERIODS={len(r['periods'])}")
print(f"DATA_STATUS={r['data_status']}")
