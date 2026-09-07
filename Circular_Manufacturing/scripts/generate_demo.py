from pathlib import Path
import csv, json, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from circular_battery.data.demo import demo_periods

out = Path(__file__).resolve().parents[1] / "data" / "demo" / "lifecycle_periods.csv"
out.parent.mkdir(parents=True, exist_ok=True)
rows = demo_periods()
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].__dict__.keys()))
    w.writeheader()
    for row in rows:
        w.writerow(row.__dict__)
print(f"WROTE {out}")
