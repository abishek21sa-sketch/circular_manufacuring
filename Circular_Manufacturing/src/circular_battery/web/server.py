from __future__ import annotations
import json, mimetypes, os, re, uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from circular_battery.web.service import (
    reference_payload,optimize_payload,frontier_payload,stress_payload,
    phase567_payload,lifecycle_payload,reverse_logistics_payload,production_plan_payload,phase10_payload,
    v1_health,v1_ready,v1_about,create_scenario_payload,list_scenarios_payload,get_scenario_payload,
    delete_scenario_payload,create_run_payload,list_runs_payload,get_run_payload,audit_payload,
    import_scenario_payload,validate_reference_bundle_payload,governance_reference_bundle_payload,workbench_v12_payload,
    circular_mass_reference_service_payload,circular_mass_decision_payload,
    public_reference_summary_payload,public_reference_facilities_payload,
)
from circular_battery.platform.contracts import success,failure
from circular_battery.platform.errors import PlatformError
from circular_battery.platform.service import get_enterprise_service
from circular_battery.web.auth import (
    AuthenticationError,
    DeploymentConfigurationError,
    load_auth_config,
    required_role,
    validate_server_configuration,
)

ROOT=Path(__file__).resolve().parents[3]
DIST=ROOT/"web"/"dist"
MAX_BODY_BYTES=2_000_000
MAX_REQUEST_TARGET_BYTES=16_384
REQUEST_ID_PATTERN=re.compile(r"^[A-Za-z0-9._-]{1,64}$")

class Handler(BaseHTTPRequestHandler):
    server_version="MaterialCircularityStudio/1.2.1"

    def _request_id(self):
        candidate=self.headers.get("X-Request-ID","")
        return candidate if REQUEST_ID_PATTERN.fullmatch(candidate) else uuid.uuid4().hex[:16]

    def _security_headers(self,request_id):
        self.send_header("X-Request-ID",request_id)
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Referrer-Policy","no-referrer")
        self.send_header("X-Frame-Options","DENY")
        self.send_header("Content-Security-Policy","default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'")
        self.send_header("Permissions-Policy","geolocation=(), microphone=(), camera=()")
        self.send_header("Access-Control-Allow-Origin",os.getenv("CIRCULAR_CORS_ORIGIN","*"))
        self.send_header("Access-Control-Allow-Methods","GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Authorization,Content-Type,X-Request-ID")

    def _json(self,obj,status=200,request_id=None,envelope=False):
        request_id=request_id or self._request_id()
        payload=success(obj,request_id=request_id) if envelope else obj
        raw=json.dumps(payload,indent=2,default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store")
        self._security_headers(request_id)
        self.end_headers()
        self.wfile.write(raw)

    def _error(self,code,message,status,request_id,details=None,extra_headers=None):
        payload=failure(code,message,request_id=request_id,details=details)
        raw=json.dumps(payload,indent=2,default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store")
        for header,value in (extra_headers or {}).items(): self.send_header(header,value)
        self._security_headers(request_id)
        self.end_headers()
        self.wfile.write(raw)

    def _authorize(self,path,method,request_id):
        try:
            config=load_auth_config(bind_host=self.server.server_address[0])
            config.authorize(self.headers, required_role(path,method))
            self._actor_role=config.role if config.auth_mode=="bearer" else "local"
            return True
        except AuthenticationError as exc:
            challenge={"WWW-Authenticate":"Bearer"} if exc.status==401 else None
            self._error(exc.code,exc.message,exc.status,request_id,extra_headers=challenge)
            return False
        except DeploymentConfigurationError:
            self._error("DEPLOYMENT_MISCONFIGURED","Service deployment is not configured for this bind.",503,request_id)
            return False

    def _read_json(self):
        if self.headers.get("Transfer-Encoding"):
            raise ValueError("Chunked transfer encoding is not supported.")
        raw_len=self.headers.get("Content-Length","0")
        try: n=int(raw_len)
        except ValueError: raise ValueError("Invalid Content-Length.")
        if n<0 or n>MAX_BODY_BYTES:
            raise ValueError(f"Request body must be <= {MAX_BODY_BYTES} bytes.")
        raw=self.rfile.read(n) if n else b"{}"
        try:
            obj=json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must contain valid JSON.") from exc
        if not isinstance(obj,dict):
            raise ValueError("JSON request body must be an object.")
        return obj

    def _query_int(self,qs,key,default,max_value):
        try: value=int(qs.get(key,[default])[0])
        except (TypeError,ValueError): value=default
        return max(1,min(value,max_value))

    def do_OPTIONS(self):
        request_id=self._request_id()
        self.send_response(204)
        self.send_header("Content-Length","0")
        self._security_headers(request_id)
        self.end_headers()

    def do_GET(self):
        request_id=self._request_id()
        if len(self.path.encode("utf-8")) > MAX_REQUEST_TARGET_BYTES:
            return self._error("REQUEST_TARGET_TOO_LARGE","Request target is too large.",414,request_id)
        try:
            parsed=urlparse(self.path);path=parsed.path;qs=parse_qs(parsed.query,max_num_fields=32)
        except ValueError:
            return self._error("VALIDATION_ERROR","Too many query parameters.",422,request_id)
        if not self._authorize(path,"GET",request_id): return
        try:
            # V1 enterprise API.
            if path=="/api/v1/health": return self._json(v1_health(),request_id=request_id,envelope=True)
            if path=="/api/v1/ready": return self._json(v1_ready(),request_id=request_id,envelope=True)
            if path=="/api/v1/about": return self._json(v1_about(),request_id=request_id,envelope=True)
            if path=="/api/v1/reference": return self._json(reference_payload(),request_id=request_id,envelope=True)
            if path=="/api/v1/phase10": return self._json(phase10_payload(),request_id=request_id,envelope=True)
            if path=="/api/v1/workbench": return self._json(workbench_v12_payload(),request_id=request_id,envelope=True)
            if path=="/api/v1/circular-mass/reference": return self._json(circular_mass_reference_service_payload(),request_id=request_id,envelope=True)
            if path=="/api/v1/phase567": return self._json(phase567_payload(),request_id=request_id,envelope=True)
            if path=="/api/v1/bundles/reference/validate": return self._json(validate_reference_bundle_payload(),request_id=request_id,envelope=True)
            if path=="/api/v1/bundles/reference/governance": return self._json(governance_reference_bundle_payload(),request_id=request_id,envelope=True)
            if path=="/api/v1/public-reference/summary": return self._json(public_reference_summary_payload(),request_id=request_id,envelope=True)
            if path=="/api/v1/public-reference/facilities":
                return self._json(
                    public_reference_facilities_payload(
                        state=qs.get("state",[None])[0],
                        naics=qs.get("naics",[None])[0],
                        query=qs.get("q",[None])[0],
                        limit=self._query_int(qs,"limit",50,100),
                    ),
                    request_id=request_id,
                    envelope=True,
                )
            if path=="/api/v1/scenarios":
                return self._json(list_scenarios_payload(self._query_int(qs,"limit",50,200)),request_id=request_id,envelope=True)
            if path.startswith("/api/v1/scenarios/"):
                scenario_id=path.rsplit("/",1)[-1]
                return self._json(get_scenario_payload(scenario_id),request_id=request_id,envelope=True)
            if path=="/api/v1/runs":
                return self._json(list_runs_payload(self._query_int(qs,"limit",50,200)),request_id=request_id,envelope=True)
            if path.startswith("/api/v1/runs/"):
                run_id=path.rsplit("/",1)[-1]
                return self._json(get_run_payload(run_id),request_id=request_id,envelope=True)
            if path=="/api/v1/audit":
                return self._json(audit_payload(self._query_int(qs,"limit",100,500)),request_id=request_id,envelope=True)

            # Backwards-compatible Phase API.
            if path=="/api/health": return self._json(v1_health(),request_id=request_id)
            if path=="/api/reference": return self._json(reference_payload(),request_id=request_id)
            if path=="/api/phase567": return self._json(phase567_payload(),request_id=request_id)
            if path=="/api/lifecycle": return self._json(lifecycle_payload(),request_id=request_id)
            if path=="/api/reverse-logistics": return self._json(reverse_logistics_payload(),request_id=request_id)
            if path=="/api/production-plan": return self._json(production_plan_payload(),request_id=request_id)
            if path=="/api/phase10": return self._json(phase10_payload(),request_id=request_id)

            if not (DIST/"index.html").exists():
                return self._error("NOT_FOUND","Legacy frontend not built on this deployment -- use the separate frontend/ app instead.",404,request_id)
            target=DIST/("index.html" if path=="/" else path.lstrip("/"))
            target=target.resolve()
            dist=DIST.resolve()
            if dist not in target.parents and target!=dist:
                return self._error("INVALID_PATH","Invalid static path.",400,request_id)
            if not target.is_file():
                target=DIST/"index.html"
            raw=target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type",mimetypes.guess_type(str(target))[0] or "application/octet-stream")
            self.send_header("Content-Length",str(len(raw)))
            self.send_header("Cache-Control","no-cache" if target.name=="index.html" else "public, max-age=3600")
            self._security_headers(request_id)
            self.end_headers();self.wfile.write(raw)
        except PlatformError as e:
            self._error(e.code,e.message,e.http_status,request_id,e.details)
        except (ValueError,TypeError) as e:
            self._error("VALIDATION_ERROR",str(e),422,request_id)
        except Exception as e:
            get_enterprise_service().logger.emit("http.unhandled_error",request_id=request_id,path=path,error_type=type(e).__name__)
            self._error("INTERNAL_ERROR","Internal server error.",500,request_id)

    def do_POST(self):
        request_id=self._request_id()
        if len(self.path.encode("utf-8")) > MAX_REQUEST_TARGET_BYTES:
            return self._error("REQUEST_TARGET_TOO_LARGE","Request target is too large.",414,request_id)
        path=urlparse(self.path).path
        if not self._authorize(path,"POST",request_id): return
        try:
            payload=self._read_json()
            if path=="/api/v1/scenarios":
                return self._json(create_scenario_payload(payload),201,request_id,envelope=True)
            if path=="/api/v1/scenarios/import":
                return self._json(import_scenario_payload(payload),201,request_id,envelope=True)
            if path=="/api/v1/runs":
                return self._json(
                    create_run_payload(
                        payload,
                        request_id=request_id,
                        actor_role=getattr(self,"_actor_role","unknown"),
                    ),
                    201,
                    request_id,
                    envelope=True,
                )
            if path=="/api/v1/circular-mass/decision":
                return self._json(circular_mass_decision_payload(payload),request_id=request_id,envelope=True)

            if path=="/api/optimize": return self._json(optimize_payload(payload),request_id=request_id)
            if path=="/api/frontier": return self._json(frontier_payload(payload),request_id=request_id)
            if path=="/api/stress": return self._json(stress_payload(payload),request_id=request_id)
            self._error("NOT_FOUND","Endpoint not found.",404,request_id)
        except PlatformError as e:
            self._error(e.code,e.message,e.http_status,request_id,e.details)
        except (ValueError,TypeError) as e:
            self._error("VALIDATION_ERROR",str(e),422,request_id)
        except Exception as e:
            get_enterprise_service().logger.emit("http.unhandled_error",request_id=request_id,path=path,error_type=type(e).__name__)
            self._error("INTERNAL_ERROR","Internal server error.",500,request_id)

    def do_DELETE(self):
        request_id=self._request_id()
        if len(self.path.encode("utf-8")) > MAX_REQUEST_TARGET_BYTES:
            return self._error("REQUEST_TARGET_TOO_LARGE","Request target is too large.",414,request_id)
        path=urlparse(self.path).path
        if not self._authorize(path,"DELETE",request_id): return
        try:
            if path.startswith("/api/v1/scenarios/"):
                scenario_id=path.rsplit("/",1)[-1]
                return self._json(delete_scenario_payload(scenario_id),request_id=request_id,envelope=True)
            self._error("NOT_FOUND","Endpoint not found.",404,request_id)
        except PlatformError as e:
            self._error(e.code,e.message,e.http_status,request_id,e.details)
        except Exception as e:
            self._error("INTERNAL_ERROR","Internal server error.",500,request_id)

    def log_message(self,fmt,*args):
        # Keep console concise; structured JSONL logger retains operational events.
        print("[studio]",fmt%args)

def run(host="127.0.0.1",port=8765):
    validate_server_configuration(host)
    if not (DIST/"index.html").exists():
        # The legacy same-origin frontend (web/) is optional: the primary UI is now
        # frontend/, a separate SvelteKit app deployed independently (see README.md
        # "Deployment"). API routes below don't depend on DIST, so a missing legacy
        # build is a warning, not a startup failure -- it only means static-fallback
        # requests to this service (anything not under /api/*) will 404 instead of
        # serving the old bundle.
        print("[studio] warning: legacy web/dist not built -- static-fallback routes will 404; API routes are unaffected")
    runtime_health=get_enterprise_service().store.health()
    if (
        os.getenv("CIRCULAR_DEPLOYMENT_MODE", "local").strip().lower()=="production"
        and runtime_health.get("backend")=="postgres"
        and runtime_health.get("migration_status")!="PASS"
    ):
        raise RuntimeError("Production PostgreSQL migration is not recorded as applied.")
    server=ThreadingHTTPServer((host,int(port)),Handler)
    print(f"Material Circularity Studio V1: http://{host}:{port}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
