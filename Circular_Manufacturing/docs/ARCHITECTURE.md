# V1 Architecture

```text
External bundle / synthetic benchmark
                |
                v
       Data validation boundary
                |
      +---------+----------+
      |                    |
      v                    v
Predictive AI       Physical lifecycle
      |                    |
      +------> AI/OR bridge+
                |
                v
    Scenario generation/reduction
                |
                v
 Two-stage stochastic optimization
      |         |         |
      v         v         v
 Critical    Reverse      IE
 materials   network    planning
                |
                v
              CVRP
                |
                v
       Policy digital replay
                |
                v
   Explainable decision engine
                |
      +---------+---------+
      |                   |
      v                   v
SQLite run registry   Material Circularity Studio
      |
      v
audit + provenance + JSONL events
```

The deterministic core remains usable without an external LLM or internet connection.
