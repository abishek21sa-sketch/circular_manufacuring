import os
from circular_battery.web.server import run
from production_preflight import run_preflight

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8765"))
    if os.getenv("CIRCULAR_DEPLOYMENT_MODE", "local").strip().lower() == "production":
        preflight = run_preflight(host=host)
        if not preflight["passed"]:
            raise SystemExit("PRODUCTION_PREFLIGHT=BLOCKED; resolve artifacts/production_preflight.json before binding")
    run(host=host, port=port)
