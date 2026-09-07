# Phase 1 Engineering Methods

## Material Flow Analysis
For each planning period, manufacturing input is decomposed into product material and manufacturing scrap:

`TotalInput = ProductMaterial + ManufacturingScrap`

End-of-life material is conserved across uncollected material, second-life allocation, remanufacturing feed, recycling feed, and direct disposal:

`Returns = Uncollected + SecondLife + Remanufacture + RecyclingFeed + DirectDisposal`

Recycling feed is decomposed into recovered material and recycling loss:

`RecyclingFeed = RecoveredMaterial + RecyclingLoss`

Recovered inventory obeys:

`OpeningInventory + RecoveredMaterial + ManufacturingScrap = RecycledUse + ClosingInventory`

All terms use kilograms in Phase 1.

## Circularity / Resource Efficiency
- Collection efficiency = collected returns / total returns.
- Recovery efficiency = (second-life + remanufacturing + recovered recycling output) / collected returns.
- Recycled content rate = recovered material used / product material requirement.
- Landfill diversion = 1 - disposed material / returned material.
- Material productivity = packs produced / tonnes of total manufacturing material input.

## Circular Value Stream
Process Cycle Efficiency:

`PCE = value-added processing time / total lead time`

The recovery value stream tracks processing time, waiting time, and cumulative physical yield across collection, grading, disassembly, and recycling.

## Lifecycle Impact Accounting
Phase 1 implements an attributional activity-factor engine:

`Impact = Σ(activity quantity × impact factor)`

The bundled factors are explicitly synthetic and are not external-validation evidence.

## Validation
Unit tests independently check material balances, physical bounds, PCE reference arithmetic, cumulative recovery yield, lifecycle-impact additivity, invalid-input rejection, and evidence labels.
