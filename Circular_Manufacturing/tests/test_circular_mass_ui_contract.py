from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_circular_mass_has_dedicated_operator_surface_and_api_calls():
    html=(ROOT/'web'/'src'/'index.html').read_text(encoding='utf-8')
    ts=(ROOT/'web'/'src'/'app.ts').read_text(encoding='utf-8')
    css=(ROOT/'web'/'src'/'styles.css').read_text(encoding='utf-8')
    assert 'data-view="circular-mass"' in html
    assert 'id="circular-mass-view"' in html
    assert 'SOLVE + GATE' in html
    assert '/api/v1/circular-mass/reference' in ts
    assert '/api/v1/circular-mass/decision' in ts
    assert 'tail_risk_note' in ts
    assert '.cmass-layout' in css


def test_built_frontend_contains_circular_mass_surface():
    html=(ROOT/'web'/'dist'/'index.html').read_text(encoding='utf-8')
    js=(ROOT/'web'/'dist'/'app.js').read_text(encoding='utf-8')
    assert 'CIRCULAR-MASS' in html
    assert '/api/v1/circular-mass/decision' in js
