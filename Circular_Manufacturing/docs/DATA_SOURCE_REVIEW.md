# Data-source review and acquisition posture

Reviewed: 2026-09-06

This review covers the data needed by the circular battery manufacturing
workbench: AI/ML battery health and demand signals, plant operations, material
and supplier risk, energy and emissions factors, reverse logistics, recovery,
and benefit measurement. The machine-readable inventory is
`data/public/data_source_registry.json`.

## Decision

The repository uses a layered evidence strategy:

1. The validated EPA GHGRP extract is included as real public facility and
   environmental reference data.
2. EPA eGRID, EIA, USGS, Argonne GREET, and NASA data are legitimate public or
   research candidates for specific factors or AI experiments. They are not
   silently converted into plant observations.
3. Kaggle is a discovery channel. User-uploaded datasets are not promoted into
   the product unless the exact license, provenance, version, and assumptions
   are reviewed. The relevant EV battery quality result located in this review
   is explicitly synthetic, so it does not improve field-validity claims.
4. Commercial market-data providers can supply useful prices and forecasts,
   but access and redistribution require a paid license or contract.
5. Company, OEM, cell-maker, dismantler, recycler, MES, ERP, BMS, and plant
   historian data require the owner's authorization, security review, and a
   data-use agreement. This workstation cannot legitimately acquire those
   records.
6. The deterministic 120,000-row enterprise dataset remains the canonical
   end-to-end regression, AI/ML pipeline, IE/OR, robustness, and Gurobi stress
   benchmark until authorized plant data is available.

## Source fitness matrix

| Source channel | What it can support | Current treatment | Why it cannot replace plant data |
|---|---|---|---|
| EPA GHGRP 2023 | Facility context, industry class, reported direct emissions | Integrated and validated in `data/public/` | No schedules, yields, quality, inventory, costs, or control telemetry |
| EPA Envirofacts FRS/TRI | Facility registry, reported chemical management, waste/release context | Candidate contextual enrichment | Public reports are not complete production material balances or plant telemetry |
| DOE battery-recycling capacity context | Public recycling-industry landscape | Candidate contextual source | Context article is not a facility operating dataset |
| EPA eGRID 2023 | Grid emissions rates, generation, resource mix | Candidate contextual factor | Not a manufacturing process or utility-meter record |
| EIA SEDS | State-level industrial energy prices and consumption | Candidate prior/sensitivity factor | Aggregated by state; not the site's tariff or meter |
| USGS Mineral Commodity Summaries | Critical-mineral supply and production context | Candidate supply-risk factor | Does not expose supplier contracts, grades, lead times, or delivered prices |
| Argonne R&D GREET | Battery lifecycle energy and carbon factors | Candidate lifecycle calibration source | Versioned model factors are not measured site outcomes |
| NASA battery prognostics/research | Battery degradation, health, and remaining-life experiments | Candidate AI research source | Lab/experimental data is not production scrap, field returns, or recycler yield |
| Kaggle community datasets | Feature discovery and model prototyping | Discovery only; no current benchmark dependency | Provenance, license, synthetic generation, and representativeness vary |
| Catena-X/Battery Pass | Battery-passport and material-lineage schema | Schema/standards reference | A standard does not grant access to participating companies' records |
| Benchmark Minerals / Fastmarkets | Licensed battery-material prices and forecasts | Requires subscription | Paid terms and redistribution restrictions apply |
| Public company filings/ESG | High-level financial, capex, and sustainability context | Public aggregate only | Backward-looking and intentionally non-operational |
| Customer and company systems | MES/ERP/BMS, quality, scrap, returns, recovery, logistics, realized benefits | Requires contract and authorization | Restricted data cannot be downloaded, inferred, or represented as observed |

## GitHub disclosure wording

The project owner currently does not have authorized access to restricted plant,
recycler, OEM, commercial market, or licensed company datasets. Accordingly,
the repository must not claim field calibration, measured emissions,
commercial market truth, or realized savings. The included public extract is a
reference benchmark; the 120,000-row enterprise dataset is synthetic validation.
Any future real-data adapter must preserve source ownership, permission,
retrieval time, units, transformation lineage, licensing terms, and a separate
evidence class.

No private data, credentials, Gurobi license files, paid-data exports, or
unapproved Kaggle content belong in the repository.

## Official and discovery references

- EPA GHGRP: <https://www.epa.gov/ghgreporting/data-sets>
- EPA Envirofacts downloads: <https://www.epa.gov/enviro/data-downloads>
- DOE battery-recycling context: <https://www.energy.gov/cmei/vehicles/articles/fotw-1350-july-8-2024-2023-united-states-had-battery-recycling-facilities>
- EPA eGRID: <https://www.epa.gov/egrid/detailed-data>
- EIA State Energy Data System: <https://www.eia.gov/state/seds/>
- USGS Mineral Commodity Summaries: <https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries>
- Argonne R&D GREET Battery CF Calculator: <https://greet.anl.gov/greet_battcf>
- NASA battery prognostics data: <https://data.nasa.gov/dataset/prognostics-in-battery-health-management>
- Kaggle EV Battery QC synthetic defect dataset: <https://www.kaggle.com/datasets/kanchana1990/ev-battery-qc-synthetic-defect-dataset>
- Catena-X Battery Passport: <https://catenax-ev.github.io/docs/next/standards/CX-0160-BatteryPassport>
- Benchmark Minerals plans: <https://www.benchmarkminerals.com/plans>
- Fastmarkets products: <https://www.fastmarkets.com/products/>
