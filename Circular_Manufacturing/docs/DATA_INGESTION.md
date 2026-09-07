# External Data Ingestion

V1 accepts a directory-based scenario bundle. See `data/templates/reference_bundle`.

Validate only:

```powershell
python scripts\run_data_bundle.py data\templates\reference_bundle --validate-only
```

Run the full ingested core chain:

```powershell
python scripts\run_data_bundle.py data\templates\reference_bundle --out artifacts\bundle_report.json
```

Required files:
- `manifest.json`: product-level and recovery/planning configuration.
- `materials.csv`: BOM, cost, carbon, yield and critical-material flags.
- `periods.csv`: production, EOL returns, collection and grade mix.
- `collections.csv`: collection-node return mass, reman eligibility and coordinates.
- `facilities.csv`: candidate recovery facilities, capacity, cost, carbon and coordinates.
- `planning.csv`: demand and production capacities by period.

The ingest layer rejects missing files, malformed numeric fields, invalid probabilities, invalid recovery facility kinds and inconsistent planning horizons.

Passing ingestion means the supplied data satisfy the software contract. It does not mean the values have been independently verified.
