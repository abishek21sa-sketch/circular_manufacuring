from __future__ import annotations
import json, threading, urllib.request, urllib.error
from http.server import ThreadingHTTPServer
from circular_battery.web.server import Handler

server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
port=server.server_address[1]
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    checks={}
    for endpoint in ("/","/api/v1/health","/api/v1/ready","/api/v1/about","/api/v1/reference","/api/v1/workbench","/api/v1/bundles/reference/validate","/api/v1/bundles/reference/governance"):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{endpoint}",timeout=30) as r:
            body=r.read();checks[endpoint]={"status":r.status,"bytes":len(body),"request_id":r.headers.get("X-Request-ID")}
            if r.status!=200: raise SystemExit(1)
            if not r.headers.get("X-Content-Type-Options"): raise SystemExit(1)
    print(json.dumps(checks,indent=2))
    print("V1_LIVE_SMOKE_OK")
finally:
    server.shutdown();server.server_close();thread.join(timeout=2)
