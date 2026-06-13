# Hardware Lifecycle Intelligence Platform

A strategy/ops dashboard that unifies PCB design, fabrication, assembly, and FPGA test data into a single deployment readiness view.

Built by Anika Bajpai — draws on real experience from Northrop Grumman (cryogenic test automation), Honeywell (FPGA/ASIC verification), and Purdue PCB design research.

---

## What it does

| Phase | Data tracked |
|---|---|
| **BOM / PCB Design** | Component supply risk, lead times, lifecycle status, cost per unit |
| **Fabrication** | Yield % by board revision, defect type, fab house comparison |
| **Assembly** | Defect rate trends by batch, defect type breakdown, operator/shift analysis |
| **FPGA / Test** | Pass/fail by revision, coverage %, failure mode correlation, top failing suites |
| **Deployment Readiness** | Weighted score across all phases, go/no-go recommendation per revision |

---

## Project structure

```
hardware-lifecycle-platform/
├── data/
│   ├── lifecycle.db          # SQLite database (all phases)
│   └── synthetic/            # CSV exports for inspection
│       ├── bom.csv
│       ├── fabrication.csv
│       ├── assembly.csv
│       ├── test_results.csv
│       └── readiness.csv
├── scripts/
│   └── generate_data.py      # Generates all synthetic datasets
├── src/
│   ├── ingestion/            # (extend here) parsers for KiCAD, QuestaSim, fab CSVs
│   ├── analysis/             # (extend here) scoring logic, anomaly detection
│   └── dashboard/            # (extend here) Streamlit app
└── README.md
```

---

## Setup

```bash
pip install pandas numpy
python scripts/generate_data.py
```

---

## Extending with real data

### KiCAD BOM ingestion
KiCAD exports BOMs as CSV. Parse and load into `bom` table:
```python
import pandas as pd, sqlite3
df = pd.read_csv("my_board.csv")  # KiCAD BOM export
# map columns to schema: reference, description, manufacturer, quantity, ...
conn = sqlite3.connect("data/lifecycle.db")
df.to_sql("bom", conn, if_exists="replace", index=False)
```

### QuestaSim / regression test ingestion
Export test results log, parse pass/fail per test suite:
```python
# parse QuestaSim coverage report or custom log
# map to: unit_id, test_suite, result, coverage_pct, failure_mode
```

### Fab house CSV ingestion
Most fab houses (PCBWay, Advanced Circuits) provide yield/inspection reports as CSV.
Map to: revision, total_boards, passed, failed, primary_defect

---

## Readiness scoring formula

```python
score = (
    fab_yield_pct      * 0.30 +
    test_pass_rate_pct * 0.40 +
    avg_coverage_pct   * 0.20 +
    (100 - asm_defect_rate_pct * 10) * 0.10
)

status = "Ready" if score >= 85 else "Conditional" if score >= 70 else "Not Ready"
```

Weights are configurable — deployment strategists can tune them based on program risk tolerance.

---

## Interview talking points

- **"How do you think about tradeoffs?"** → The scoring formula makes tradeoffs explicit. A high fab yield can't compensate for low test coverage.
- **"How do you handle failure/uncertainty?"** → Assembly defect rates and test failure modes are tracked and correlated back to fabrication.
- **"Tell me about a complex system you've worked on."** → This mirrors workflows from Northrop cryogenic test automation (Python data acquisition), Honeywell FPGA regression testing (UVM/QuestaSim), and Purdue PCB research (KiCAD).
- **"Can you code?"** → Show the data pipeline: SQLite + Pandas, modular ingestion, scoring logic.
