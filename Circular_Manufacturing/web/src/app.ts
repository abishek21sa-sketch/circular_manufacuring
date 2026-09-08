type AnyObj = Record<string, any>;

const $ = (id:string) => document.getElementById(id) as HTMLElement;
let wb:AnyObj = {};
let reference:AnyObj = {};
let selectedPolicy = "";
let selectedRiskPolicy = "";
let selectedTrace = 0;
const API_BASE = String((window as any).__CIRCULAR_API_BASE__ || "").replace(/\/$/, "");

async function fetchJSON(url:string, options?:RequestInit){
  const target = url.startsWith("/api/") ? `${API_BASE}${url}` : url;
  const r=await fetch(target,options);
  const payload=await r.json();
  if(!r.ok) throw new Error(payload?.error?.message || payload?.error || `HTTP ${r.status}`);
  return payload;
}
async function fetchV1(url:string, options?:RequestInit){
  const p=await fetchJSON(url,options);
  return p?.data ?? p;
}
const money=(v:number)=>{
  const n=Number(v||0); if(Math.abs(n)>=1e6) return `$${(n/1e6).toFixed(2)}M`; if(Math.abs(n)>=1e3)return `$${(n/1e3).toFixed(1)}k`;return `$${n.toFixed(0)}`;
};
const mass=(v:number)=>{const n=Number(v||0);if(Math.abs(n)>=1e6)return `${(n/1e6).toFixed(2)}M kg`;if(Math.abs(n)>=1000)return `${(n/1000).toFixed(1)} t`;return `${n.toFixed(0)} kg`;};
const pct=(v:number)=>`${(Number(v||0)*100).toFixed(1)}%`;
const num=(v:number,d=1)=>Number(v||0).toFixed(d);
const clamp=(x:number,a:number,b:number)=>Math.max(a,Math.min(b,x));
const esc=(s:any)=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]||c));

function bindTabs(){
  document.querySelectorAll(".tab").forEach(btn=>btn.addEventListener("click",()=>{
    document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
    document.querySelectorAll(".view").forEach(x=>x.classList.remove("active-view"));
    btn.classList.add("active");
    const view=(btn as HTMLElement).dataset.view!;
    $(`${view}-view`).classList.add("active-view");
  }));
}

function renderRibbon(){
  const d=wb.decision||{};
  const chosen=wb.chosen_stochastic_policy||{};
  const plan=wb.coupled_planning?.solution||{};
  const cm=wb.coupled_critical_materials||{};
  $("global-ribbon").innerHTML=`
    <div class="ribbon-cell primary"><span>Recommended policy</span><b>${esc(String(d.recommended_policy||"—").replaceAll("_"," ").toUpperCase())}</b></div>
    <div class="ribbon-cell"><span>Decision confidence</span><b>${pct(d.confidence)}</b></div>
    <div class="ribbon-cell"><span>Expected total cost</span><b>${money(chosen.expected_total_cost)}</b></div>
    <div class="ribbon-cell"><span>CVaR operating cost</span><b>${money(chosen.cvar_operating_cost)}</b></div>
    <div class="ribbon-cell"><span>Coupled plan service</span><b>${pct(plan.service_level)}</b></div>
    <div class="ribbon-cell"><span>Critical recovered share</span><b>${pct(cm.recovered_share)}</b></div>`;
}

// ---------------- MATERIALS ----------------
function materialInspector(kind:string){
  const p5=reference.phase567?.phase5||{};
  const circ=p5.circularity_metrics||{};
  const chosen=wb.chosen_stochastic_policy||{};
  const plan=wb.coupled_planning?.solution||{};
  const lookup:AnyObj={
    virgin:{title:"Virgin material",text:"Primary feed closes the material balance after recovered output, internal scrap recovery and inventory are applied.",facts:[["Expected virgin",mass(chosen.expected_virgin_kg)],["Plan virgin",mass(plan.total_virgin_kg)],["Dependency",pct(plan.ie_metrics?.virgin_material_dependency||plan.total_virgin_kg/(plan.total_virgin_kg+plan.total_recovered_use_kg||1))],["Evidence","OPTIMIZED"]]},
    manufacturing:{title:"Manufacturing",text:"Production converts virgin and recovered material into battery packs while manufacturing scrap re-enters the circular feed contract.",facts:[["Pack mass",`${p5.design?.pack_mass_kg||400} kg`],["Scrap rate",pct(p5.design?.manufacturing_scrap_rate||0)],["Plan service",pct(plan.service_level)],["Evidence","IE + MATERIAL BALANCE"]]},
    use:{title:"Use cohort",text:"Installed batteries create the future return pool. The return-hazard model translates cohort state into expected EOL feedstock.",facts:[["Demand forecast",`${Math.round(wb.bridge?.demand_prediction_packs||0)} packs`],["Return forecast",`${Math.round(wb.bridge?.return_prediction_packs||0)} packs`],["Second-life share",pct(wb.bridge?.derived_second_life_share||0)],["Evidence","PREDICTED"]]},
    returns:{title:"End-of-life returns",text:"Returns are filtered by collection and second-life allocation before becoming recovery-system feed.",facts:[["Base returns",mass(wb.bridge?.derived_base_returns_kg?.[0]||0)],["Collection design","87.0%"],["Routing batch",mass(wb.coupled_routing?.routing_input?.collected_batch_kg||0)],["Evidence","PREDICTED → OPTIMIZED"]]},
    recovery:{title:"Recovery system",text:"Facility activation, processing yields, reman eligibility, disposal policy and N−1 resilience constrain usable recovery output.",facts:[["Technical recovery",pct(circ.technical_recovery_rate||0)],["Circular pathway",pct(circ.circular_pathway_rate||0)],["Open facilities",Object.entries(chosen.open_facilities||{}).filter(([,v])=>v).map(([k])=>k).join(", ")||"—"],["Evidence","OPTIMIZED"]]},
    recovered:{title:"Recovered feed",text:"Expected recovery output and recovered manufacturing scrap become the material availability consumed by the coupled IE production plan.",facts:[["Recovered plan use",mass(plan.total_recovered_use_kg)],["Recycled content",pct(plan.recycled_content_rate)],["Critical recovered share",pct(wb.coupled_critical_materials?.recovered_share||0)],["Evidence","COUPLED V1.2"]]},
  };
  const x=lookup[kind]||lookup.recovered;
  $("material-inspector-title").textContent=x.title;
  $("material-inspector").innerHTML=`<p>${x.text}</p><div class="inspector-grid">${x.facts.map((f:any)=>`<div><small>${f[0]}</small><b>${f[1]}</b></div>`).join("")}</div>`;
}

function renderMaterials(){
  const p5=reference.phase567?.phase5||{};
  const plan=wb.coupled_planning?.solution||{};
  const nodes:any[]=[
    ["virgin",120,245,66,"Virgin","PRIMARY"],
    ["manufacturing",340,245,78,"Manufacturing","PRODUCTION"],
    ["use",570,245,64,"Use","COHORT"],
    ["returns",790,245,66,"Returns","EOL"],
    ["recovery",790,420,78,"Recovery","SORT / PROCESS"],
    ["recovered",340,420,76,"Recovered","SECONDARY FEED"],
  ];
  const edges:any[]=[
    [186,245,260,245,"",mass(plan.total_virgin_kg)],
    [418,245,506,245,"",`${Math.round((plan.total_regular_packs||0)+(plan.total_overtime_packs||0))} packs`],
    [634,245,724,245,"return",`${Math.round(wb.bridge?.return_prediction_packs||0)} forecast returns`],
    [790,311,790,342,"return","collection + grading"],
    [712,420,416,420,"",mass(plan.total_recovered_use_kg)],
    [340,344,340,323,"","scrap recirculation"],
  ];
  let h=`<defs><marker id="mArr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#9be5bd"/></marker><marker id="rArr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#ff9568"/></marker></defs>`;
  edges.forEach(([x1,y1,x2,y2,cls,label])=>h+=`<path class="lifecycle-edge ${cls}" marker-end="url(#${cls?"rArr":"mArr"})" d="M${x1} ${y1}L${x2} ${y2}"/><text class="edge-label" x="${(x1+x2)/2}" y="${(y1+y2)/2-12}">${esc(label)}</text>`);
  nodes.forEach(([id,x,y,r,title,sub],i)=>h+=`<g class="lifecycle-node ${id==="recovered"?"active":""}" data-kind="${id}"><circle cx="${x}" cy="${y}" r="${r}"/><text class="node-title" x="${x}" y="${y-3}">${title}</text><text class="node-sub" x="${x}" y="${y+17}">${sub}</text></g>`);
  $("materials-flow").innerHTML=h;
  $("materials-flow").querySelectorAll(".lifecycle-node").forEach(el=>el.addEventListener("click",()=>{
    $("materials-flow").querySelectorAll(".lifecycle-node").forEach(x=>x.classList.remove("active"));el.classList.add("active");materialInspector((el as HTMLElement).dataset.kind!);
  }));
  materialInspector("recovered");
  const materials=(p5.design?.materials||[]).filter((m:AnyObj)=>m.critical);
  $("material-ledger").innerHTML=materials.map((m:AnyObj)=>`<div class="material-row-v12"><div><strong>${esc(m.name.toUpperCase())}</strong><small>${num(m.kg_per_pack,1)} kg/pack</small></div><div class="yield-track"><i style="width:${clamp(Number(m.recycling_yield)*100,0,100)}%"></i></div><em>${pct(m.recycling_yield)}</em></div>`).join("");
  const circ=p5.circularity_metrics||{};
  $("materials-footer").innerHTML=[
    ["Material productivity",pct(circ.material_productivity)],["Collection efficiency",pct(circ.collection_efficiency)],["Technical recovery",pct(circ.technical_recovery_rate)],
    ["Critical recovery",pct(circ.critical_material_recovery_rate)],["Plan recycled content",pct(plan.recycled_content_rate)],["Max balance residual",`${Number(p5.max_material_balance_error_kg||0).toExponential(1)} kg`]
  ].map(x=>`<div><small>${x[0]}</small><b>${x[1]}</b></div>`).join("");
}

// ---------------- NETWORK ----------------
function renderNetwork(){
  const rl=reference.phase567?.phase6?.reverse_logistics||{};
  const flows=rl.flows||[];const opened=rl.opened_facilities||{};
  const coords:AnyObj={Chicago:[150,160],Detroit:[190,430],Columbus:[455,475],Indianapolis:[410,225],"R-Chicago":[760,145],"R-Ohio":[935,410],"M-Detroit":[755,475],"M-Indiana":[720,285]};
  const max=Math.max(1,...flows.map((f:AnyObj)=>Number(f.kg)));
  let h=`<defs><marker id="netA" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#9be5bd"/></marker></defs>`;
  flows.forEach((f:AnyObj)=>{const a=coords[f.collection],b=coords[f.facility];if(!a||!b)return;const w=1.4+8*Number(f.kg)/max;h+=`<path class="network-edge ${f.pathway==='reman'?'reman':''}" marker-end="url(#netA)" style="stroke-width:${w}px" d="M${a[0]} ${a[1]} C${(a[0]+b[0])/2} ${a[1]},${(a[0]+b[0])/2} ${b[1]},${b[0]} ${b[1]}"><title>${esc(f.collection)} → ${esc(f.facility)} ${mass(f.kg)}</title></path>`;});
  ["Chicago","Detroit","Columbus","Indianapolis"].forEach(n=>{const [x,y]=coords[n];h+=`<g><circle class="network-node" cx="${x}" cy="${y}" r="27"/><text class="svg-label" x="${x}" y="${y-39}">${n}</text><text class="svg-sub" x="${x}" y="${y+4}">COLLECT</text></g>`;});
  ["R-Chicago","R-Ohio","M-Detroit","M-Indiana"].forEach(n=>{const [x,y]=coords[n];const o=Number(opened[n]||0)===1;h+=`<g><rect class="network-facility ${o?'open':'closed'}" x="${x-36}" y="${y-27}" width="72" height="54" rx="5"/><text class="svg-label" x="${x}" y="${y-39}">${n}</text><text class="svg-sub" x="${x}" y="${y+4}">${o?'OPEN':'CLOSED'}</text></g>`;});
  $("network-svg").innerHTML=h;
  $("network-kpis").innerHTML=[["Collected",mass(rl.collected_kg)],["Processed",mass(rl.processed_kg)],["Disposed",mass(rl.disposed_kg)],["Network CO₂e",mass(rl.total_kgco2e)]].map(x=>`<div><small>${x[0]}</small><b>${x[1]}</b></div>`).join("");
  const facilityNames=["R-Chicago","R-Ohio","M-Detroit","M-Indiana"];
  $("facility-list").innerHTML=facilityNames.map(n=>{const o=Number(opened[n]||0)===1;const throughput=flows.filter((f:AnyObj)=>f.facility===n).reduce((a:number,b:AnyObj)=>a+Number(b.kg),0);return `<div class="facility-row"><div><b>${n}</b><small>${mass(throughput)} routed</small></div><span class="facility-state ${o?'open':'closed'}">${o?'OPEN':'CLOSED'}</span></div>`}).join("");
  const rows=[...flows].sort((a:AnyObj,b:AnyObj)=>b.kg-a.kg).slice(0,8);
  $("network-flow-table").innerHTML=`<table class="data-table"><thead><tr><th>COLLECTION</th><th>FACILITY</th><th>PATHWAY</th><th>MASS</th><th>DISTANCE</th><th>TRANSPORT COST</th></tr></thead><tbody>${rows.map((f:AnyObj)=>`<tr><td>${f.collection}</td><td><strong>${f.facility}</strong></td><td><span class="tag">${String(f.pathway).toUpperCase()}</span></td><td>${mass(f.kg)}</td><td>${num(f.distance_km,1)} km</td><td>${money(f.transport_cost)}</td></tr>`).join("")}</tbody></table>`;
}

// ---------------- PLAN ----------------
function renderPlan(){
  const plan=wb.coupled_planning?.solution||{};const rows=plan.period_rows||[];const sc=wb.coupled_planning?.scenario||{};
  $("plan-summary").innerHTML=[["Service",pct(plan.service_level)],["Recycled content",pct(plan.recycled_content_rate)],["Virgin input",mass(plan.total_virgin_kg)],["Recovered use",mass(plan.total_recovered_use_kg)],["Overtime",`${num(plan.total_overtime_packs,0)} packs`],["Constraint residual",Number(plan.max_constraint_violation||0).toExponential(1)]].map(x=>`<div><small>${x[0]}</small><b>${x[1]}</b></div>`).join("");
  const maxDemand=Math.max(1,...rows.map((r:AnyObj)=>r.demand_packs));
  $("plan-periods").innerHTML=rows.map((r:AnyObj,i:number)=>`<article class="period-card"><div class="period-card-head"><div><span>P${r.period}</span><b>${num(r.demand_packs,0)} demand</b></div><small>${pct(r.regular_capacity_utilization)} regular util.</small></div><div class="bar-group"><div class="bar-row"><label>Demand</label><div class="bar-bg"><i style="width:${100*r.demand_packs/maxDemand}%"></i></div><b>${num(r.demand_packs,0)}</b></div><div class="bar-row capacity"><label>Regular</label><div class="bar-bg"><i style="width:${100*r.regular_packs/maxDemand}%"></i></div><b>${num(r.regular_packs,0)}</b></div><div class="bar-row recovered"><label>Recovered</label><div class="bar-bg"><i style="width:${100*r.recycled_content_rate}%"></i></div><b>${pct(r.recycled_content_rate)}</b></div></div><div class="period-facts"><div><small>Virgin</small><b>${mass(r.virgin_kg)}</b></div><div><small>Recovered</small><b>${mass(r.recovered_use_kg)}</b></div><div><small>FG inventory</small><b>${num(r.closing_fg_inventory_packs,0)} packs</b></div><div><small>Recovery supply</small><b>${mass(sc.recovered_supply_kg?.[i]||0)}</b></div></div></article>`).join("");
  const ie=wb.coupled_planning?.ie_metrics||{};
  $("plan-metrics").innerHTML=[["Aggregate capacity util.",pct(ie.aggregate_capacity_utilization)],["Regular capacity util.",pct(ie.regular_capacity_utilization)],["Overtime share",pct(ie.overtime_share)],["Virgin dependency",pct(ie.virgin_material_dependency)],["Demand source","AI → OR bridge"]].map(x=>`<div><small>${x[0]}</small><b>${x[1]}</b></div>`).join("");
}

// ---------------- STRATEGY ----------------
function candidateByName(name:string){return (wb.frontier?.candidates||[]).find((x:AnyObj)=>x.policy===name)||{};}
function isNondominated(name:string){return (wb.frontier?.nondominated||[]).some((x:AnyObj)=>x.policy===name);}
function renderStrategyInspector(p:AnyObj){
  const settings=p.settings||{};const actions=[] as string[];Object.entries(p.open_facilities||{}).forEach(([k,v])=>{if(v)actions.push(`Open ${k}`)});Object.entries(p.expansion_units||{}).forEach(([k,v])=>{if(Number(v)>0)actions.push(`Add ${v} expansion unit(s) at ${k}`)});
  $("strategy-inspector").innerHTML=`<p class="eyebrow">${isNondominated(p.policy)?'NONDOMINATED POLICY':'FEASIBLE POLICY'}</p><h2>${esc(String(p.policy||'').replaceAll('_',' '))}</h2><div class="policy-kpis"><div><small>Expected cost</small><b>${money(p.expected_total_cost)}</b></div><div><small>CVaR</small><b>${money(p.cvar_operating_cost)}</b></div><div><small>Carbon</small><b>${mass(p.expected_carbon_kgco2e)} CO₂e</b></div><div><small>Virgin</small><b>${mass(p.expected_virgin_kg)}</b></div><div><small>Service</small><b>${pct(p.expected_service_level)}</b></div><div><small>N−1 reserve</small><b>${settings.n_minus_one_min_capacity_kg?mass(settings.n_minus_one_min_capacity_kg):'OFF'}</b></div></div><ul class="action-list">${actions.map(a=>`<li>${a}</li>`).join('')||'<li>No facility activation required.</li>'}</ul><div class="divider"></div><div class="side-heading"><span>QUICK DETERMINISTIC RE-SOLVE</span><b>test one lever set</b></div><div style="margin-top:12px"><label style="font-size:9px;color:var(--muted)">Collection rate <input id="q-collection" type="range" min=".60" max=".98" step=".01" value=".86" style="width:100%;accent-color:var(--acid)"></label><label style="display:block;margin-top:10px;font-size:9px;color:var(--muted)">Recycle yield <input id="q-yield" type="range" min=".72" max=".98" step=".01" value=".90" style="width:100%;accent-color:var(--acid)"></label><label style="display:block;margin-top:10px;font-size:9px;color:var(--muted)">Carbon price <input id="q-carbon" type="range" min="0" max="2" step=".1" value=".2" style="width:100%;accent-color:var(--acid)"></label><button id="q-solve" style="margin-top:14px;width:100%;padding:10px;border:1px solid var(--acid);background:transparent;color:var(--acid);cursor:pointer;font-size:9px;letter-spacing:.08em">RE-SOLVE</button><div id="q-result" style="margin-top:10px;color:var(--muted);font-size:10px;line-height:1.5"></div></div>`;
  $("q-solve").addEventListener("click",async()=>{const b=$("q-solve") as HTMLButtonElement;b.disabled=true;b.textContent="SOLVING…";try{const body={scenario:{collection_rate:Number(($("q-collection") as HTMLInputElement).value),recycle_yield:Number(($("q-yield") as HTMLInputElement).value)},carbon_price_per_kg:Number(($("q-carbon") as HTMLInputElement).value)};const r=await fetchJSON('/api/optimize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});$("q-result").innerHTML=`OPTIMAL · ${money(r.solution.total_cost)} · ${mass(r.solution.virgin_kg)} virgin · ${pct(r.solution.recycled_content_rate)} recycled`; }catch(e:any){$("q-result").innerHTML=`<span class="error">${esc(e.message)}</span>`}finally{b.disabled=false;b.textContent="RE-SOLVE";}});
}
function renderStrategy(){
  const pts=wb.frontier?.candidates||[];if(!pts.length)return;selectedPolicy=wb.decision?.recommended_policy||pts[0].policy;
  const W=1080,H=560,L=86,R=35,T=45,B=72;const xs=pts.map((p:AnyObj)=>p.expected_total_cost),ys=pts.map((p:AnyObj)=>p.expected_carbon_kgco2e);let xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);const xp=(x:number)=>L+(x-xmin)/(xmax-xmin||1)*(W-L-R);const yp=(y:number)=>H-B-(y-ymin)/(ymax-ymin||1)*(H-T-B);
  let h="";for(let i=0;i<=4;i++){const x=L+(W-L-R)*i/4;const val=xmin+(xmax-xmin)*i/4;h+=`<line class="strategy-grid" x1="${x}" y1="${T}" x2="${x}" y2="${H-B}"/><text class="strategy-label" x="${x}" y="${H-B+22}" text-anchor="middle">${money(val)}</text>`;const y=T+(H-T-B)*i/4;const yval=ymax-(ymax-ymin)*i/4;h+=`<line class="strategy-grid" x1="${L}" y1="${y}" x2="${W-R}" y2="${y}"/><text class="strategy-label" x="${L-10}" y="${y+3}" text-anchor="end">${(yval/1e6).toFixed(2)}M</text>`;}h+=`<line class="strategy-axis" x1="${L}" y1="${H-B}" x2="${W-R}" y2="${H-B}"/><line class="strategy-axis" x1="${L}" y1="${T}" x2="${L}" y2="${H-B}"/><text class="strategy-axis-label" x="${(L+W-R)/2}" y="${H-18}" text-anchor="middle">EXPECTED TOTAL COST</text><text class="strategy-axis-label" transform="translate(22 ${(T+H-B)/2}) rotate(-90)" text-anchor="middle">EXPECTED CARBON (kg CO₂e)</text>`;
  pts.forEach((p:AnyObj)=>{const nd=isNondominated(p.policy),sel=p.policy===selectedPolicy;const r=7+8*clamp((p.cvar_operating_cost-Math.min(...pts.map((x:AnyObj)=>x.cvar_operating_cost)))/(Math.max(...pts.map((x:AnyObj)=>x.cvar_operating_cost))-Math.min(...pts.map((x:AnyObj)=>x.cvar_operating_cost))||1),0,1);h+=`<circle class="strategy-point ${nd?'nd':''} ${sel?'selected':''}" data-policy="${p.policy}" cx="${xp(p.expected_total_cost)}" cy="${yp(p.expected_carbon_kgco2e)}" r="${r}"><title>${p.policy} · ${money(p.expected_total_cost)} · ${mass(p.expected_virgin_kg)} virgin</title></circle><text class="strategy-policy-label" x="${xp(p.expected_total_cost)}" y="${yp(p.expected_carbon_kgco2e)-r-8}">${String(p.policy).replaceAll('_',' ')}</text>`;});
  $("strategy-svg").innerHTML=h;$("strategy-svg").querySelectorAll(".strategy-point").forEach(el=>el.addEventListener("click",()=>{selectedPolicy=(el as HTMLElement).dataset.policy!;renderStrategy();}));renderStrategyInspector(candidateByName(selectedPolicy));
  $("strategy-table").innerHTML=`<table class="data-table"><thead><tr><th>POLICY</th><th>STATUS</th><th>COST</th><th>CARBON</th><th>VIRGIN</th><th>CVAR</th><th>SERVICE</th></tr></thead><tbody>${pts.map((p:AnyObj)=>`<tr><td><strong>${String(p.policy).replaceAll('_',' ')}</strong></td><td><span class="tag">${isNondominated(p.policy)?'NONDOMINATED':'FEASIBLE'}</span></td><td>${money(p.expected_total_cost)}</td><td>${mass(p.expected_carbon_kgco2e)}</td><td>${mass(p.expected_virgin_kg)}</td><td>${money(p.cvar_operating_cost)}</td><td>${pct(p.expected_service_level)}</td></tr>`).join('')}</tbody></table>`;
  renderStochasticValue();
}

function renderStochasticValue(){
  const v=wb.stochastic_information_value||{};
  if(!$("stochastic-value"))return;
  $("stochastic-value").innerHTML=`
    <div class="value-card"><small>Risk-neutral stochastic program</small><b>${money(v.risk_neutral_stochastic_program_cost)}</b><em>RP · optimize before uncertainty resolves</em></div>
    <div class="value-card"><small>Expected-value policy in scenarios</small><b>${money(v.expected_result_of_expected_value_cost)}</b><em>EEV · deterministic policy replayed</em></div>
    <div class="value-card highlight"><small>Value of stochastic solution</small><b>${money(v.value_of_stochastic_solution)}</b><em>${pct(v.vss_percent_of_rp)} of RP cost</em></div>
    <div class="value-card highlight"><small>Perfect-information ceiling</small><b>${money(v.expected_value_of_perfect_information)}</b><em>EVPI · ${pct(v.evpi_percent_of_rp)} of RP cost</em></div>
    <div class="value-explainer"><strong>Interpretation.</strong> VSS is the expected cost avoided by optimizing against the scenario distribution instead of using one average-future policy. EVPI is the maximum expected amount perfect advance information could be worth. ${esc(v.scope||"")}</div>`;
}

// ---------------- ROUTES ----------------
function renderRoutes(){
  const r=wb.coupled_routing||{};const coords:AnyObj={"North-Collector":[480,125],"West-Collector":[200,285],"South-Collector":[410,510],"East-Collector":[760,355],"Northeast-Collector":[620,100],"Southwest-Collector":[190,490]};const depot=[470,330];let h="";const colors=["#9be5bd","#ff9568","#d7f56f","#8fc8d8","#c8a6ff","#f1c27d"];
  (r.routes||[]).forEach((route:any[],ri:number)=>{const pts=route.map((name:string)=>name.includes('hub')?depot:coords[name]).filter(Boolean);for(let i=0;i<pts.length-1;i++)h+=`<line x1="${pts[i][0]}" y1="${pts[i][1]}" x2="${pts[i+1][0]}" y2="${pts[i+1][1]}" style="stroke:${colors[ri%colors.length]};stroke-width:3;opacity:.8"/>`;});
  h+=`<circle class="route-depot" cx="${depot[0]}" cy="${depot[1]}" r="25"/><text class="route-label" x="${depot[0]}" y="${depot[1]-38}">${esc(r.routing_input?.primary_hub||'hub')}</text><text class="route-pickup" x="${depot[0]}" y="${depot[1]+4}">DEPOT</text>`;
  Object.entries(coords).forEach(([name,xy]:any)=>{const q=r.routing_input?.customer_pickups_kg?.[name]||0;h+=`<circle class="route-node" cx="${xy[0]}" cy="${xy[1]}" r="22"/><text class="route-label" x="${xy[0]}" y="${xy[1]-34}">${name.replace('-Collector','')}</text><text class="route-pickup" x="${xy[0]}" y="${xy[1]+4}">${mass(q)}</text>`;});$("route-svg").innerHTML=h;
  $("route-side").innerHTML=`<p class="eyebrow">COUPLED ROUTING SOLUTION</p><div class="policy-kpis"><div><small>Vehicles</small><b>${r.vehicles_used}</b></div><div><small>Distance</small><b>${num(r.total_distance_km,1)} km</b></div><div><small>Route cost</small><b>${money(r.objective_cost)}</b></div><div><small>GHG</small><b>${num(r.total_kgco2e,1)} kgCO₂e</b></div></div><p style="color:var(--muted);font-size:10px;line-height:1.5;margin-top:14px">${esc(r.routing_input?.source_contract||'')}</p><div class="divider"></div><div class="side-heading"><span>TOURS</span><b>${r.vehicles_used} exact tours</b></div>${(r.routes||[]).map((route:any[],i:number)=>{const load=r.route_loads_kg?.[i]||0;return `<div class="tour-card"><strong>TOUR ${i+1} · ${mass(load)}</strong><p>${route.map((x:string)=>x.replace('-Collector','')).join(' → ')} · ${num(r.route_distances_km?.[i],1)} km</p><div class="capacity-track"><i style="width:${clamp(load/40000*100,0,100)}%"></i></div></div>`}).join('')}`;
}

// ---------------- AI ----------------
function lowerIsBetter(key:string){return key!=="recovery";}
function renderAI(){
  const ev=wb.ai_evidence||{};const xai=wb.ai_explainability||{};const specs:any[]=[['demand','Demand forecast','MAE','mae'],['returns','EOL return hazard','Brier','brier'],['recovery','Recovery pathway','Macro-F1','macro_f1'],['scrap','Scrap-rate model','MAE','mae']];
  $("ai-model-grid").innerHTML=specs.map(([k,title,label,key])=>{const e=ev[k]||{};const m=Number(e.metrics?.[key]||0),b=Number(e.baseline_metrics?.[key]||0);const improvement=lowerIsBetter(k)?(b?1-m/b:0):(b<1?(m-b)/(1-b):0);const score=lowerIsBetter(k)?clamp((1-m/(b||1))*100,0,100):clamp(improvement*100,0,100);return `<article class="ai-card"><h3>${title}</h3><div class="ai-score">${k==='demand'?m.toFixed(1):m.toFixed(4)} <small>${label}</small></div><div class="comparison-track"><i style="width:${score}%"></i><em style="left:72%"></em></div><p>Baseline ${k==='demand'?b.toFixed(1):b.toFixed(4)} · held-out improvement signal ${score.toFixed(1)}% · ${esc(e.evidence_class||'')}</p></article>`}).join('');
  const vals=[['Demand',Number(wb.bridge?.demand_prediction_packs||0),''],['Returns',Number(wb.bridge?.return_prediction_packs||0),'returns'],['Routed batch',Number(wb.coupled_routing?.routing_input?.collected_batch_kg||0)/400,'recovered']];const max=Math.max(1,...vals.map(x=>Number(x[1])));$("ai-state-svg").innerHTML=vals.map((v:any,i:number)=>{const x=100+i*215,h=210*Number(v[1])/max;return `<rect class="ai-state-bar ${v[2]}" x="${x}" y="${260-h}" width="105" height="${h}"/><text x="${x+52}" y="285" fill="#9db0a5" font-size="10" text-anchor="middle">${v[0]}</text><text x="${x+52}" y="${245-h}" fill="#f0f4f1" font-size="16" text-anchor="middle">${Math.round(Number(v[1]))}</text>`}).join('');
  const imp=xai.recovery?.feature_importance_permutation_macro_f1||{};const entries=Object.entries(imp).sort((a:any,b:any)=>Math.abs(b[1])-Math.abs(a[1])).slice(0,6);const maxImp=Math.max(.0001,...entries.map(([,v]:any)=>Math.abs(Number(v))));$("ai-explain-panel").innerHTML=`<div class="panel-label">RECOVERY MODEL DRIVERS</div><div class="xai-list">${entries.map(([k,v]:any)=>`<div class="xai-row"><span>${esc(k.replaceAll('_',' '))}</span><div class="xai-track"><i style="width:${100*Math.abs(Number(v))/maxImp}%"></i></div><b>${Number(v).toFixed(3)}</b></div>`).join('')}</div><div class="divider"></div><div class="inspector-grid"><div><small>Demand interval coverage</small><b>${pct(xai.demand?.empirical_holdout_coverage||0)}</b></div><div><small>Return calibration ECE</small><b>${Number(xai.returns?.expected_calibration_error||0).toFixed(4)}</b></div><div><small>Recovery confidence gap</small><b>${Number(xai.recovery?.mean_confidence_gap||xai.recovery?.confidence_gap||0).toFixed(3)}</b></div><div><small>Scrap top driver</small><b>${esc(Object.keys(xai.scrap?.feature_importance||{})[0]||'—')}</b></div></div>`;
}

// ---------------- RISK ----------------
function replayByPolicy(name:string){return (wb.policy_replay||[]).find((x:AnyObj)=>x.policy===name)||{};}
function renderRisk(){
  const policies=wb.policy_replay||[];if(!policies.length)return;if(!selectedRiskPolicy)selectedRiskPolicy=policies[0].policy;$("risk-policy-tabs").className="risk-tabs";$("risk-policy-tabs").innerHTML=policies.map((p:AnyObj)=>`<button class="risk-tab ${p.policy===selectedRiskPolicy?'active':''}" data-risk="${p.policy}">${String(p.policy).replaceAll('_',' ')}</button>`).join('');$("risk-policy-tabs").querySelectorAll('.risk-tab').forEach(el=>el.addEventListener('click',()=>{selectedRiskPolicy=(el as HTMLElement).dataset.risk!;renderRisk();}));
  const p=replayByPolicy(selectedRiskPolicy);const costs=(p.scenario_rows||[]).map((r:AnyObj)=>Number(r.total_cost)).filter((x:number)=>Number.isFinite(x));const probs=(p.scenario_rows||[]).map((r:AnyObj)=>Number(r.probability||0));const W=1100,H=520,L=70,R=30,T=45,B=65;const min=Math.min(...costs),max=Math.max(...costs);const bins=12;const counts=new Array(bins).fill(0);costs.forEach((x:number,i:number)=>{const b=Math.min(bins-1,Math.floor((x-min)/(max-min||1)*bins));counts[b]+=probs[i]||1/costs.length;});const maxC=Math.max(.001,...counts);const p90=Number(p.p90_total_cost||0),cvar=Number(p.cvar95_total_cost||0);let h=`<line class="risk-axis" x1="${L}" y1="${H-B}" x2="${W-R}" y2="${H-B}"/>`;counts.forEach((c:number,i:number)=>{const x=L+(W-L-R)*i/bins+4,bw=(W-L-R)/bins-8,bh=(H-T-B)*c/maxC;const center=min+(max-min)*(i+.5)/bins;h+=`<rect class="hist-bar ${center>=p90?'tail':''}" x="${x}" y="${H-B-bh}" width="${bw}" height="${bh}"/><text class="risk-text" x="${x+bw/2}" y="${H-B+18}" text-anchor="middle">${i%2===0?money(center):''}</text>`;});const xp=(x:number)=>L+(x-min)/(max-min||1)*(W-L-R);h+=`<line class="risk-line" x1="${xp(p90)}" y1="${T}" x2="${xp(p90)}" y2="${H-B}"/><text class="risk-text" x="${xp(p90)+5}" y="${T+15}">P90 ${money(p90)}</text><text class="risk-text" x="${L}" y="${H-18}">SCENARIO TOTAL COST →</text>`;$("risk-svg").innerHTML=h;$("risk-quantiles").innerHTML=`<span class="risk-quantile">tail threshold ${money(p90)} · CVaR95 ${money(cvar)}</span>`;
  $("risk-side").innerHTML=`<p class="eyebrow">${String(p.policy||'').replaceAll('_',' ').toUpperCase()}</p><h2>Policy replay</h2>${[["Expected cost",money(p.expected_total_cost)],["P90 cost",money(p.p90_total_cost)],["CVaR95",money(p.cvar95_total_cost)],["Expected carbon",mass(p.expected_carbon_kgco2e)],["Expected virgin",mass(p.expected_virgin_kg)],["Service",pct(p.expected_service_level)],["Emergency probability",pct(p.emergency_recovery_probability)]].map(x=>`<div class="risk-stat"><span>${x[0]}</span><b>${x[1]}</b></div>`).join('')}`;
  $("risk-table").innerHTML=`<table class="data-table"><thead><tr><th>POLICY</th><th>EXPECTED COST</th><th>P90</th><th>CVAR95</th><th>CARBON</th><th>VIRGIN</th><th>EMERGENCY</th></tr></thead><tbody>${policies.map((x:AnyObj)=>`<tr><td><strong>${String(x.policy).replaceAll('_',' ')}</strong></td><td>${money(x.expected_total_cost)}</td><td>${money(x.p90_total_cost)}</td><td>${money(x.cvar95_total_cost)}</td><td>${mass(x.expected_carbon_kgco2e)}</td><td>${mass(x.expected_virgin_kg)}</td><td>${pct(x.emergency_recovery_probability)}</td></tr>`).join('')}</tbody></table>`;
}



// ---------------- CIRCULAR-MASS ----------------
let cmassReference:AnyObj = {};
function renderCircularMassReference(){
  const rows=cmassReference.scenarios||[];
  $("cmass-scenario-table").innerHTML=`<table class="data-table"><thead><tr><th>SCENARIO</th><th>PROBABILITY</th><th>DEMAND</th><th>HYDRO YIELD</th><th>DIRECT YIELD</th><th>PYRO YIELD</th></tr></thead><tbody>${rows.map((r:AnyObj)=>`<tr><td><strong>${esc(r.name)}</strong></td><td>${pct(r.probability)}</td><td>${mass(r.demand_kg)}</td>${(r.yields||[]).map((y:number)=>`<td>${pct(y)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
}
function renderCircularMassDecision(d:AnyObj){
  const sol=d.solution||{};
  $("cmass-gate").textContent=d.decision_gate||"—";
  $("cmass-status").classList.toggle("blocked",d.decision_gate!=="AUTHORIZED");
  $("cmass-status").innerHTML=`<strong>${esc(d.decision_id||"—")}</strong> · ${esc(d.operator_message||"")}`;
  $("cmass-kpis").innerHTML=[
    ["Expected recovered",mass(sol.expected_recovered_kg)],
    ["Recycled content",pct(sol.recycled_content_share)],
    ["Expected shortage",mass(sol.expected_shortage_kg)],
    ["CVaR shortage",mass(sol.cvar_shortage_kg)],
    ["Objective",money(sol.objective)]
  ].map(x=>`<div class="cmass-kpi"><small>${x[0]}</small><b>${x[1]}</b></div>`).join('');
  $("cmass-facilities").innerHTML=(d.facility_actions||[]).map((f:AnyObj)=>`<div class="cmass-facility ${f.open?'open':''}"><small>${f.open?'ACTIVE RECOVERY PATH':'NOT SELECTED'}</small><h3>${esc(f.facility)}</h3><b>${mass(f.route_kg)}</b><p>${f.open?'Facility is used in the optimized first-stage recovery plan.':'No recovery mass routed through this option.'}</p></div>`).join('');
  $("cmass-checks").innerHTML=Object.entries(d.checks||{}).map(([k,v])=>`<div class="cmass-check"><span>${esc(k.replaceAll('_',' '))}</span><b class="${v?'pass':'fail'}">${v?'PASS':'FAIL'}</b></div>`).join('');
  $("cmass-boundary").innerHTML=`<div class="cmass-boundary-note">${esc(d.evidence?.class||'')}</div><div class="cmass-boundary-note">${esc(d.tail_risk_note||'')}</div><div class="cmass-boundary-note">Field calibration: <strong>${esc(d.evidence?.field_calibration||'PENDING')}</strong><br>Realized operational benefits: <strong>${esc(d.evidence?.realized_operational_benefits||'NOT CLAIMED')}</strong></div><div class="cmass-boundary-note">Human review required: <strong>${d.human_review_required?'YES':'NO'}</strong></div>`;
}
async function solveCircularMass(){
  const b=$("cmass-solve") as HTMLButtonElement;
  b.disabled=true;b.textContent='SOLVING…';
  try{
    const body={min_recycled_content:Number(($("cmass-floor") as HTMLInputElement).value),risk_aversion:Number(($("cmass-risk") as HTMLInputElement).value),max_virgin_share:Number(($("cmass-virgin") as HTMLInputElement).value)};
    const d=await fetchV1('/api/v1/circular-mass/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    renderCircularMassDecision(d);
  }catch(e:any){$("cmass-status").classList.add("blocked");$("cmass-status").textContent=e.message;}
  finally{b.disabled=false;b.textContent='SOLVE + GATE';}
}
function bindCircularMass(){$("cmass-solve").addEventListener('click',solveCircularMass);}
async function loadCircularMass(){cmassReference=await fetchV1('/api/v1/circular-mass/reference');renderCircularMassReference();await solveCircularMass();}

// ---------------- TRACE ----------------
function traceSummary(t:AnyObj){const c=t.component;const map:AnyObj={DemandForecaster:'Forecast monthly battery demand.',ReturnHazardModel:'Estimate probability-weighted EOL returns.',ScrapPredictor:'Estimate manufacturing scrap fraction.',RecoveryPathwayClassifier:'Estimate second-life / reman / recycle / disposal shares.',ScenarioBridge:'Convert predictions into correlated uncertain futures.',TwoStageStochasticMILP:'Choose first-stage recovery capacity with scenario recourse and CVaR.',CriticalMaterialPlanner:'Optimize Li/Ni/Co/graphite recovered and virgin sourcing.',CVRP:'Build exact capacity-feasible collection tours.',StrategicSensitivity:'Stress decision levers and observe policy changes.',PolicyReplay:'Replay fixed policies on unreduced futures.',DecisionEngine:'Score feasible nondominated strategies and retain human approval.'};return map[c]||'Computational decision stage.';}
function renderTraceInspector(){const t=(wb.decision_trace||[])[selectedTrace];if(!t)return;$("trace-inspector").innerHTML=`<p class="eyebrow">STEP ${String(t.step).padStart(2,'0')} · ${esc(t.evidence)}</p><h2>${esc(t.component)}</h2><p>${traceSummary(t)}</p><div class="inspector-grid"><div><small>Evidence class</small><b>${esc(t.evidence)}</b></div><div><small>Unit</small><b>${esc(t.unit)}</b></div></div><div class="trace-output"><pre>${esc(JSON.stringify(t.output,null,2))}</pre></div>`;}
function renderTrace(){const trace=wb.decision_trace||[];$("trace-list").innerHTML=trace.map((t:AnyObj,i:number)=>`<div class="trace-step ${i===selectedTrace?'active':''}" data-trace="${i}"><div class="num">${String(t.step).padStart(2,'0')}</div><div><b>${esc(t.component)}</b><small>${traceSummary(t)}</small></div><div class="trace-evidence">${esc(t.evidence)}</div></div>`).join('');$("trace-list").querySelectorAll('.trace-step').forEach(el=>el.addEventListener('click',()=>{selectedTrace=Number((el as HTMLElement).dataset.trace);renderTrace();}));renderTraceInspector();$("coupling-contract").innerHTML=(wb.integration_contract||[]).map((r:AnyObj)=>`<div class="integration-row"><b>${esc(r.from)}</b><span class="arrow">→</span><b>${esc(r.to)}</b><span class="integration-status">${esc(r.status)}</span><p>${esc(r.detail)}</p></div>`).join('');}

// ---------------- RUNS ----------------
async function inspectRun(runId:string){
  try{
    const r=await fetchV1(`/api/v1/runs/${runId}`);
    document.querySelectorAll(".run-row-click").forEach(x=>x.classList.toggle("active",(x as HTMLElement).dataset.run===runId));
    const d=r.report?.decision||{};
    const prov=r.report?.platform_run||{};
    const actions=(d.action||[]) as string[];
    $("run-report").innerHTML=`
      <div class="run-report-grid">
        <div><small>Run</small><b>${esc(r.run_id)}</b></div>
        <div><small>Scenario</small><b>${esc(r.scenario_id||"—")}</b></div>
        <div><small>Policy</small><b>${esc(String(d.recommended_policy||"—").replaceAll("_"," ").toUpperCase())}</b></div>
        <div><small>Confidence</small><b>${pct(d.confidence||0)}</b></div>
        <div><small>Runtime</small><b>${r.runtime_seconds==null?"—":num(r.runtime_seconds,2)+" s"}</b></div>
        <div><small>Decision hash</small><b>${esc(String(r.decision_hash_sha256||"—").slice(0,24))}${r.decision_hash_sha256?"…":""}</b></div>
        <div><small>Code fingerprint</small><b>${esc(String(r.code_fingerprint_sha256||prov.code_fingerprint_sha256||"—").slice(0,24))}${(r.code_fingerprint_sha256||prov.code_fingerprint_sha256)?"…":""}</b></div>
        <div><small>Status</small><b>${esc(r.status)}</b></div>
      </div>
      <div class="run-report-actions">
        <div class="report-box"><h3>Decision actions</h3><ul>${actions.length?actions.map(a=>`<li>${esc(a)}</li>`).join(""):"<li>No explicit facility action recorded.</li>"}</ul></div>
        <div class="report-box"><h3>Runtime provenance</h3><pre>${esc(JSON.stringify(prov.runtime_environment||{},null,2))}</pre></div>
      </div>`;
  }catch(e:any){
    $("run-report").innerHTML=`<div class="error">${esc(e.message)}</div>`;
  }
}

async function refreshRuns(){
  try{
    const rows=await fetchV1('/api/v1/runs?limit=15');
    $("run-table").innerHTML=rows.length?`<table class="data-table"><thead><tr><th>RUN</th><th>SCENARIO</th><th>STATUS</th><th>RUNTIME</th><th>DECISION HASH</th></tr></thead><tbody>${rows.map((r:AnyObj)=>`<tr class="run-row-click" data-run="${r.run_id}"><td><strong>${r.run_id}</strong></td><td>${r.scenario_id||'—'}</td><td><span class="tag">${r.status}</span></td><td>${r.runtime_seconds==null?'—':num(r.runtime_seconds,1)+' s'}</td><td>${r.decision_hash_sha256?String(r.decision_hash_sha256).slice(0,18)+'…':'—'}</td></tr>`).join('')}</tbody></table>`:`<div style="padding:18px;color:var(--muted);font-size:11px">No persisted runs yet.</div>`;
    $("run-table").querySelectorAll(".run-row-click").forEach(el=>el.addEventListener("click",()=>inspectRun((el as HTMLElement).dataset.run!)));
  }catch(e:any){
    $("run-table").innerHTML=`<div class="error" style="padding:15px">${esc(e.message)}</div>`;
  }
}
function bindRuns(){$("run-execute").addEventListener('click',async()=>{const b=$("run-execute") as HTMLButtonElement;b.disabled=true;b.textContent='EXECUTING…';$("run-status").textContent='Running the complete AI → stochastic OR → routing → replay → recommendation chain. Keep this tab open.';try{const body={name:($("run-name") as HTMLInputElement).value,seed:Number(($("run-seed") as HTMLInputElement).value),raw_n:Number(($("run-raw") as HTMLInputElement).value),reduced_k:Number(($("run-reduced") as HTMLInputElement).value),include_sensitivity:false};const r=await fetchV1('/api/v1/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});$("run-status").innerHTML=`REGISTERED <strong>${r.run_id}</strong> · ${r.status} · policy ${String(r.report?.decision?.recommended_policy||'—').replaceAll('_',' ')} · ${num(r.runtime_seconds,1)} s`;await refreshRuns();await inspectRun(r.run_id);}catch(e:any){$("run-status").innerHTML=`<span class="error">${esc(e.message)}</span>`}finally{b.disabled=false;b.textContent='EXECUTE + REGISTER';}});}

// ---------------- EVIDENCE ----------------
function renderEvidence(){const models=wb.math_inventory||[];$("math-inventory").innerHTML=`<div class="math-row header"><span>MODEL</span><span>ROLE</span><span>VARS</span><span>CONSTRAINTS</span><span>SOLVER</span><span>VERIFICATION</span></div>${models.map((m:AnyObj)=>`<div class="math-row"><b>${esc(m.model)}</b><span>${esc(m.role)}</span><strong>${m.variables}${m.integer_variables?` / ${m.integer_variables} int`:''}</strong><strong>${m.constraints}${m.objectives?` / ${m.objectives} obj`:''}</strong><span>${esc(m.solver)}</span><p>${esc(m.verification)}</p></div>`).join('')}`;$("model-boundaries").innerHTML=(wb.known_model_boundaries||[]).map((x:string,i:number)=>`<div class="boundary"><b style="color:var(--orange);margin-right:8px">0${i+1}</b>${esc(x)}</div>`).join('');}

async function boot(){
  bindTabs();bindRuns();bindCircularMass();
  try{
    [wb,reference]=await Promise.all([fetchV1('/api/v1/workbench'),fetchJSON('/api/reference')]);
    renderRibbon();renderMaterials();renderNetwork();renderPlan();renderStrategy();renderRoutes();renderAI();renderRisk();renderTrace();renderEvidence();await Promise.all([refreshRuns(),loadCircularMass()]);
  }catch(e:any){document.body.insertAdjacentHTML('afterbegin',`<div class="error" style="padding:12px;background:#2a1715">${esc(e.message)}</div>`);}
}
boot();
