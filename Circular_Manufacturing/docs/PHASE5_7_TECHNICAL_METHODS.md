# Phases 5–7 Technical Methods

## Phase 5 — Circular Manufacturing Domain Engine

### Product/material model
The reference product is a synthetic NMC-like battery pack with a 400 kg bill of materials. Material records explicitly carry:
- kg per pack;
- virgin and secondary-material cost factors;
- virgin and secondary-material GHG factors;
- technical recycling yield;
- critical-material flag.

### Manufacturing material balance
For material \(m\) and period \(t\):

`ManufacturingInput[m,t] = EmbeddedProduct[m,t] / (1 - ScrapRate)`

`ManufacturingScrap[m,t] = ManufacturingInput[m,t] - EmbeddedProduct[m,t]`

Units: kg.

### End-of-life recovery balance
Returned material is split by collection and grade-weighted recovery pathway.

`Returns = Uncollected + SecondLife + RemanRetained + RecycledOutput + RecyclingLoss + DirectDisposal`

Remanufacturing losses are explicitly routed into recycling feed rather than disappearing from the model.

### Circularity indicators
Implemented indicators include:
- material productivity;
- manufacturing scrap rate;
- collection efficiency;
- technical recovery rate;
- circular-pathway rate;
- landfill/loss rate;
- critical-material recovery rate.

### Lifecycle comparison
Recovered material is compared against virgin-equivalent material using explicit per-material cost and GHG factors. The output is labeled **MODELED COMPARATIVE IMPACT**, never realized savings.

---

## Phase 6 — Closed-Loop Reverse Logistics

### Decision problem
Collected end-of-life battery material must be assigned from collection regions to candidate remanufacturing/recycling facilities or disposal.

### Variables
- `x[c,f] >= 0`: kg routed from collection node `c` to facility `f`.
- `d[c] >= 0`: kg disposed from collection node `c`.
- `y[f] ∈ {0,1}`: whether candidate facility `f` is active.

### Objective
Minimize:

`facility fixed cost + transport cost + processing cost + disposal cost`

Transport cost uses kg-km.

### Constraints
1. Collection-node mass balance.
2. Remanufacturing flow cannot exceed reman-eligible return mass.
3. Facility throughput <= capacity × open binary.
4. Network disposal <= configured maximum disposal share.
5. Non-negativity and binary facility domains.

### Environmental accounting
Transport emissions are calculated using kg-km factors. Processing and disposal emissions are separately retained.

### Verification
- post-solve node balance;
- facility-capacity audit;
- disposal-policy audit;
- binary-domain audit;
- exact one-node/one-facility oracle case.

---

## Phase 7 — Industrial Engineering Production & Circular Inventory Planning

### Decision problem
Determine regular production, overtime production, virgin material use, recovered-material use, recovered-material inventory, finished-goods inventory, and shortage across multiple planning periods.

### Variables
Per period:
- regular production [packs];
- overtime production [packs];
- virgin material [kg];
- recovered material used [kg];
- recovered-material ending inventory [kg];
- finished-goods ending inventory [packs];
- unmet demand emergency slack [packs].

### Material requirement
`Virgin + RecoveredUse = PackMass × (RegularProduction + OvertimeProduction)`

### Recovered inventory
`OpeningRecoveredInventory + RecoveredSupply = RecoveredUse + ClosingRecoveredInventory`

### Finished-goods balance
`OpeningFG + Production + Shortage = Demand + ClosingFG`

### Capacity
`RegularProduction <= RegularCapacity`

`OvertimeProduction <= OvertimeCapacity`

### Circular-content bounds
`MinCircularContent × MaterialRequirement <= RecoveredUse`

`RecoveredUse <= MaxCircularContent × MaterialRequirement`

### Safety stock
Each non-final period must hold a configured fraction of the next period's demand as finished-goods inventory.

### Objective
Minimize regular/overtime production, virgin/recovered material, inventory holding, and emergency shortage costs.

Shortage carries a deliberately high penalty so it remains an emergency feasibility variable instead of an economically preferred policy.

### IE outputs
- service level;
- regular and aggregate capacity utilization;
- overtime share;
- average finished-goods inventory;
- average recovered-material inventory;
- material productivity;
- recycled content;
- virgin-material dependency.

### Phase integration
Phase 5 computes technically recoverable external material and internal manufacturing scrap. Phase 6 determines the share of external circular material the reverse network can physically process. Phase 7 receives:

`AvailableCircularFeed = NetworkCapture × ExternalTechnicalRecovery + InternalScrapRecovery`

Thus the three phases form one computational chain.
