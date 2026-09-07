from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(*args):
    print('RUNNING:', ' '.join(map(str,args)), flush=True)
    subprocess.run([str(a) for a in args],cwd=ROOT,check=True)
def main():
    py=sys.executable
    run(py,'scripts/build_frontend.py')
    run(py,'-m','pytest','tests/test_signature_algorithm.py','tests/test_circular_mass_product.py','tests/test_circular_mass_ui_contract.py','tests/test_v1_api.py','tests/test_phase8_advanced_or.py','-q')
    run(py,'scripts/circular_mass_evidence.py')
    run(py,'scripts/circular_mass_product_evidence.py')
    run(py,'scripts/gurobi_circular_mass_check.py')
    run(py,'scripts/gurobi_phase3_check.py')
    run(py,'scripts/gurobi_phase10_check.py')
    run(py,'scripts/validate_governed_bundle.py','data/templates/reference_bundle','--require-lineage','--out','artifacts/governed_reference_bundle.json')
    run(py,'scripts/validate_database_migrations.py','--out','artifacts/database_migration_validation.json')
    run(py,'scripts/validate_public_reference_dataset.py','data/public/epa_ghgrp_2023_facilities.csv','data/public/epa_ghgrp_2023_metadata.json','--out','artifacts/public_reference_validation.json')
    run(py,'scripts/validate_data_source_registry.py','--out','artifacts/data_source_registry_validation.json')
    run(py,'scripts/generate_synthetic_enterprise_dataset.py')
    run(py,'scripts/validate_synthetic_enterprise_dataset.py')
    run(py,'scripts/synthetic_enterprise_gurobi_benchmark.py')
    run(py,'scripts/validate_production_attestations.py','--out','artifacts/production_attestation_validation.json')
    run(py,'scripts/production_preflight.py')
    run(py,'scripts/release_readiness.py')
    run(py,'scripts/validate_engineering_readiness.py','--out','artifacts/engineering_readiness.json')
    print('CIRCULAR_MASS_WINDOWS_ACCEPTANCE=PASS')
if __name__=='__main__': main()
