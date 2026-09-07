# Synthetic Enterprise Dataset

The repository includes a deterministic synthetic benchmark at
`data/synthetic/enterprise_120k/`.

It contains 120,000 complete operational observations across twelve case
families, 1,000 scenarios per case, and ten periods per scenario: nominal, seasonal peak, demand
downturn, scrap spike, quality degradation, transport disruption, facility
outage, material shortage, grid-carbon spike, return surge, low remanufacture
eligibility, and service-infeasible capacity.

The canonical `observations.csv` is complete and bounded for software,
optimization, and model-pipeline tests. Each row includes public-data context
strata (`public_context_sector`, `public_context_emissions_tier`) and a
bounded industrial trend profile. These are distributional context features,
not measurements of the referenced facilities. The separate `adversarial_cases.csv`
fixture contains intentionally invalid examples for negative validation tests;
it must not be merged into the canonical dataset.

## Generate, validate, and solve

From the inner repository directory:

```powershell
& .venv\Scripts\python.exe scripts\generate_synthetic_enterprise_dataset.py
& .venv\Scripts\python.exe scripts\validate_synthetic_enterprise_dataset.py
& .venv\Scripts\python.exe scripts\synthetic_enterprise_gurobi_benchmark.py
```

The benchmark explicitly requests `solver_backend="gurobi"` and is intended
for the user's Academic Gurobi research/engineering environment. Gurobi
credentials are never stored in the dataset or repository.

## Domain basis

The generator uses bounded engineering relationships rather than pretending a
public source contains all plant-operating variables. Its scope and
plausibility checks are informed by:

- EPA GHGRP facility-level industrial emissions data:
  https://www.epa.gov/ghgreporting/data-sets
- Argonne National Laboratory R&D GREET Battery Carbon Footprint Calculator:
  https://greet.anl.gov/greet_battcf
- U.S. Department of Energy battery-recycling capacity context:
  https://www.energy.gov/cmei/vehicles/articles/fotw-1350-july-8-2024-2023-united-states-had-battery-recycling-facilities
- International Energy Agency Global EV Outlook 2026 battery trends:
  https://www.iea.org/reports/global-ev-outlook-2026/electric-vehicle-batteries
- U.S. Energy Information Administration Manufacturing Energy Consumption Survey:
  https://www.eia.gov/consumption/manufacturing/

The EPA extract is used to sample sector and emissions-tier context with
replacement; facility identifiers and names are not copied. IEA and EIA
sources inform conservative trend-profile assumptions: demand growth,
recycling-feedstock lag, manufacturing scale-up, and energy-price stress.
These sources do not turn generated values into measured plant data or a
forecast. The fixed seed, manifest, lineage, file hashes, case catalog, and
validator report make the benchmark reproducible as synthetic validation only.

## Claim boundary

This dataset supports software regression, solver stress testing, scenario
coverage, model-pipeline development, and demonstration. It cannot prove
customer-site calibration, environmental performance, financial savings,
regulatory compliance, or realized operational benefit. Those remain external
production gates.
