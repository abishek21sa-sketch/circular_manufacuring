from circular_battery.decision.circular_mass_bridge import (
    build_circular_mass_decision,
    circular_mass_reference_payload,
)
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_circular_mass_reference_exposes_formulation_and_validation():
    p=circular_mass_reference_payload()
    assert p["algorithm"]=="CIRCULAR-MASS"
    assert len(p["facilities"])==3
    assert len(p["scenarios"])==3
    assert p["validation"] is not None
    assert all(p["validation"]["checks"].values())


def test_circular_mass_decision_is_governed_and_review_only():
    d=build_circular_mass_decision()
    assert d["decision_gate"]=="AUTHORIZED"
    assert d["human_review_required"] is True
    assert d["solution"]["status"]=="OPTIMAL"
    assert d["checks"]["mass_balance_feasible"]
    assert d["decision_id"].startswith("CMASS-")
    assert "no autonomous" in d["operator_message"].lower()


def test_circular_mass_policy_input_changes_recovery_plan():
    low=build_circular_mass_decision(min_recycled_content=.20)
    high=build_circular_mass_decision(min_recycled_content=.65)
    assert high["solution"]["expected_recovered_kg"] > low["solution"]["expected_recovered_kg"]
    assert sum(high["solution"]["open_facilities"].values()) >= sum(low["solution"]["open_facilities"].values())


def test_standalone_runtime_exposes_engineering_decision_surfaces():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from product_runtime import _html

    html = _html()
    assert "Scenario outcomes and CVaR tail" in html
    assert "Objective decomposition" in html
    assert "Governance checks" in html
    assert "Download evidence JSON" in html


def test_standalone_runtime_hides_unexpected_error_details(monkeypatch):
    import sys
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer
    sys.path.insert(0, str(ROOT / "scripts"))
    import product_runtime as runtime

    def explode(_params):
        raise RuntimeError("secret internal solver detail")

    monkeypatch.setattr(runtime, "compute", explode)
    server=ThreadingHTTPServer(("127.0.0.1",0),runtime.Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/decision?min_recycled_content=.2",timeout=5)
        except urllib.error.HTTPError as exc:
            body=exc.read().decode()
            assert exc.code==500
            assert "secret internal solver detail" not in body
            assert exc.headers["X-Request-ID"]
        else:
            raise AssertionError("expected HTTP 500")
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
