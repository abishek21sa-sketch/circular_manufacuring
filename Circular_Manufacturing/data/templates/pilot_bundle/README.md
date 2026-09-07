# Governed plant-pilot bundle

This directory is a contract template, not plant evidence. A pilot submission
must contain the five scenario CSV files and a `manifest.json` with complete
UTC lineage:

- `source_system`
- `source_owner`
- `facility_id`
- `as_of_utc`
- `data_classification`

Run the generic quality gate first:

```powershell
& .venv\Scripts\python.exe scripts\validate_governed_bundle.py .\data\pilot\PLANT_ID --require-lineage
```

Then run the pilot-specific gate:

```powershell
& .venv\Scripts\python.exe scripts\validate_pilot_bundle.py .\data\pilot\PLANT_ID
```

The pilot gate rejects synthetic/reference labels. It validates declarations
and file integrity but cannot prove that a plant or supplier reported truthful
measurements; that requires owner approval and source-system controls.
