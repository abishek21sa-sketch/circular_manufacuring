import argparse, json
from pathlib import Path
from circular_battery.platform.service import get_enterprise_service
from circular_battery.ingestion.bundle import run_bundle, validate_bundle

svc=get_enterprise_service()
parser=argparse.ArgumentParser(description="Circular Manufacturing V1 enterprise platform CLI")
sub=parser.add_subparsers(dest="command",required=True)

c=sub.add_parser("create-scenario")
c.add_argument("--name",default="CLI decision experiment")
c.add_argument("--seed",type=int,default=20260817)
c.add_argument("--raw-n",type=int,default=40)
c.add_argument("--reduced-k",type=int,default=6)
c.add_argument("--no-sensitivity",action="store_true")

r=sub.add_parser("run")
r.add_argument("--scenario-id")
r.add_argument("--name",default="CLI decision experiment")
r.add_argument("--seed",type=int,default=20260817)
r.add_argument("--raw-n",type=int,default=40)
r.add_argument("--reduced-k",type=int,default=6)
r.add_argument("--no-sensitivity",action="store_true")

sub.add_parser("list-runs")
sub.add_parser("list-scenarios")

g=sub.add_parser("get-run");g.add_argument("run_id")
b=sub.add_parser("bundle");b.add_argument("directory",type=Path);b.add_argument("--validate-only",action="store_true")

args=parser.parse_args()
if args.command=="create-scenario":
    out=svc.create_scenario({"name":args.name,"seed":args.seed,"raw_n":args.raw_n,"reduced_k":args.reduced_k,"include_sensitivity":not args.no_sensitivity})
elif args.command=="run":
    payload={"name":args.name,"seed":args.seed,"raw_n":args.raw_n,"reduced_k":args.reduced_k,"include_sensitivity":not args.no_sensitivity}
    out=svc.execute(payload=payload,scenario_id=args.scenario_id)
elif args.command=="list-runs": out=svc.store.list_runs()
elif args.command=="list-scenarios": out=svc.store.list_scenarios()
elif args.command=="get-run": out=svc.store.get_run(args.run_id)
elif args.command=="bundle":
    out=validate_bundle(args.directory) if args.validate_only else run_bundle(args.directory)
else: raise SystemExit(2)
print(json.dumps(out,indent=2,default=str))
