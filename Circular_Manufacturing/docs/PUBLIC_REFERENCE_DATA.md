# Public industrial reference data

This release includes a curated extract from the U.S. EPA Greenhouse Gas
Reporting Program (GHGRP) 2023 Data Summary Spreadsheets. EPA describes GHGRP
as facility-level data from large industrial sources and reports that 7,544
facilities reported direct emissions for 2023. The official dataset page also
provides the downloadable spreadsheets and explains that the data are reported
under EPA’s verification process.

Source page: <https://www.epa.gov/ghgreporting/data-sets>

Source archive:
<https://www.epa.gov/system/files/other-files/2024-10/2023_data_summary_spreadsheets.zip>

The project extract is:

- `data/public/epa_ghgrp_2023_facilities.csv`
- `data/public/epa_ghgrp_2023_metadata.json`
- `artifacts/public_reference_validation.json`

The extract contains public facility identifiers, location fields, industry
classification, and reported direct emissions in metric tons CO2e. It does not
contain recovery yields, production schedules, costs, inventory, quality data,
or control-system telemetry. It is therefore a public benchmark/reference
dataset, not a governed customer-plant pilot dataset and not realized-benefit
evidence.

The reproducible ingestion command is `scripts/ingest_epa_ghgrp.py`; the
acceptance validator is `scripts/validate_public_reference_dataset.py`. Source
archive and workbook SHA-256 values are retained in the metadata record.

The ingestion tool uses the optional data extra, which is separate from the
production runtime:

```powershell
& .venv\Scripts\python.exe -m pip install -e ".[data]" --no-deps
```

The wider public, research, Kaggle, commercial, and private-data review is
recorded in `docs/DATA_SOURCE_REVIEW.md` and
`data/public/data_source_registry.json`. The EPA extract is the only included
real operational-context source; all other unavailable sources remain
explicitly classified as candidates, discovery-only, paid, or permissioned.
