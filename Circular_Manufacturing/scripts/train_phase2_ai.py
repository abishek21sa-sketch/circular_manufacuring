from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from circular_battery.ai.training import train_all
root=Path(__file__).resolve().parents[1]
models,evidence,datasets=train_all(root/"artifacts"/"models", persist_models=False)
print(json.dumps(evidence,indent=2))
print("PHASE2_AI_TRAINING_COMPLETE")
