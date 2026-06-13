"""
generate_data.py
Generates realistic synthetic datasets for all hardware lifecycle phases:
  - PCB Design (BOM + netlist risk)
  - Fabrication (yield by revision)
  - Assembly (defect logs by batch)
  - FPGA/Test (test results + coverage)
"""

import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/lifecycle.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ─────────────────────────────────────────────
# 1. PCB DESIGN — Bill of Materials
# ─────────────────────────────────────────────
def gen_bom():
    components = [
        ("U1",  "Xilinx XC7A35T FPGA",        "Xilinx",       1,  "FPGA",         42.50, 18, "Active"),
        ("U2",  "STM32F407 MCU",               "STMicro",      1,  "MCU",          8.20,  12, "Active"),
        ("U3",  "TPS62130 Buck Converter",     "TI",           2,  "Power",        1.85,  6,  "Active"),
        ("U4",  "ADC128S102 ADC",              "TI",           1,  "Analog",       3.40,  52, "NRND"),
        ("U5",  "LMK04828 Clock IC",           "TI",           1,  "Clock",        18.70, 24, "Active"),
        ("C1",  "100nF 0402 Decoupling Cap",   "Murata",       48, "Passive",      0.02,  4,  "Active"),
        ("C2",  "10uF 0805 Bulk Cap",          "TDK",          12, "Passive",      0.15,  4,  "Active"),
        ("R1",  "10k 0402 Resistor",           "Yageo",        32, "Passive",      0.01,  4,  "Active"),
        ("J1",  "USB Type-C Connector",        "Molex",        1,  "Connector",    0.85,  16, "Active"),
        ("J2",  "40-pin FPC Connector",        "Hirose",       2,  "Connector",    1.20,  26, "Active"),
        ("L1",  "4.7uH Inductor",              "Bourns",       3,  "Passive",      0.45,  8,  "Active"),
        ("X1",  "25MHz Crystal",               "ABRACON",      1,  "Oscillator",   0.95,  14, "Active"),
        ("U6",  "IS42S32400F SDRAM",           "ISSI",         1,  "Memory",       3.10,  36, "Active"),
        ("U7",  "W25Q128JV Flash",             "Winbond",      1,  "Memory",       1.60,  10, "Active"),
        ("D1",  "BAT54 Schottky Diode",        "Vishay",       4,  "Discrete",     0.12,  6,  "Active"),
    ]
    rows = []
    for ref, desc, mfr, qty, cat, unit_cost, lead_wk, status in components:
        risk = "Low"
        if lead_wk > 20:
            risk = "High"
        elif lead_wk > 12 or status == "NRND":
            risk = "Medium"
        rows.append({
            "reference": ref,
            "description": desc,
            "manufacturer": mfr,
            "quantity": qty,
            "category": cat,
            "unit_cost_usd": unit_cost,
            "extended_cost_usd": round(unit_cost * qty, 2),
            "lead_time_weeks": lead_wk,
            "lifecycle_status": status,
            "supply_risk": risk,
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 2. FABRICATION — Yield by Board Revision
# ─────────────────────────────────────────────
def gen_fabrication():
    revisions = ["Rev A", "Rev B", "Rev C", "Rev D", "Rev E"]
    fab_houses = ["PCBWay", "Advanced Circuits", "TTM Technologies"]
    defect_types = ["Open trace", "Short circuit", "Via misalignment",
                    "Soldermask bleed", "Impedance out-of-spec", "Copper void"]
    rows = []
    base_yield = 0.62
    for i, rev in enumerate(revisions):
        yield_rate = min(0.97, base_yield + i * 0.07 + np.random.normal(0, 0.02))
        panels = random.randint(8, 20)
        boards_per_panel = 4
        total = panels * boards_per_panel
        passed = int(total * yield_rate)
        failed = total - passed
        date = datetime(2024, 8, 1) + timedelta(weeks=i * 6)
        for _ in range(failed):
            rows.append({
                "revision": rev,
                "fab_house": random.choice(fab_houses),
                "date": date.strftime("%Y-%m-%d"),
                "total_boards": total,
                "passed": passed,
                "failed": failed,
                "yield_pct": round(yield_rate * 100, 1),
                "primary_defect": random.choice(defect_types),
                "layer_count": 6,
                "panel_count": panels,
            })
        if not failed:
            rows.append({
                "revision": rev,
                "fab_house": random.choice(fab_houses),
                "date": date.strftime("%Y-%m-%d"),
                "total_boards": total,
                "passed": passed,
                "failed": 0,
                "yield_pct": round(yield_rate * 100, 1),
                "primary_defect": None,
                "layer_count": 6,
                "panel_count": panels,
            })
    return pd.DataFrame(rows).drop_duplicates(subset=["revision"])


# ─────────────────────────────────────────────
# 3. ASSEMBLY — Defect Logs by Batch
# ─────────────────────────────────────────────
def gen_assembly():
    defect_types = ["Solder bridge", "Tombstone", "Cold joint",
                    "Missing component", "Wrong polarity", "Insufficient solder"]
    locations = ["U1 pin 14", "J2 pin 3", "C1 cluster", "R1 array",
                 "U3 pad 6", "J1 shell", "L1 lead", "U4 BGA"]
    rows = []
    for batch in range(1, 16):
        date = datetime(2024, 10, 1) + timedelta(weeks=batch - 1)
        qty = random.randint(10, 25)
        defect_rate = max(0.02, 0.18 - batch * 0.009 + np.random.normal(0, 0.02))
        defects = int(qty * defect_rate)
        for d in range(defects):
            rows.append({
                "batch_id": f"BATCH-{batch:03d}",
                "date": date.strftime("%Y-%m-%d"),
                "units_assembled": qty,
                "defect_type": random.choice(defect_types),
                "location": random.choice(locations),
                "defect_rate_pct": round(defect_rate * 100, 1),
                "rework_required": random.choice([True, True, False]),
                "operator_id": f"OP-{random.randint(1,5):02d}",
                "shift": random.choice(["Day", "Evening"]),
            })
        if not defects:
            rows.append({
                "batch_id": f"BATCH-{batch:03d}",
                "date": date.strftime("%Y-%m-%d"),
                "units_assembled": qty,
                "defect_type": None,
                "location": None,
                "defect_rate_pct": 0.0,
                "rework_required": False,
                "operator_id": f"OP-{random.randint(1,5):02d}",
                "shift": random.choice(["Day", "Evening"]),
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 4. FPGA / TEST — Regression Results
# ─────────────────────────────────────────────
def gen_test_results():
    test_suites = [
        "USB_TX_Basic", "USB_RX_Basic", "USB_Bulk_Transfer",
        "AHB_Lite_Slave", "Clock_Domain_Cross", "Power_Sequencing",
        "Temp_Stress_25C", "Temp_Stress_n40C", "Temp_Stress_85C",
        "FIFO_Overflow", "FIFO_Underflow", "DMA_Transfer",
        "SPI_Loopback", "UART_Stress", "FPGA_Bitstream_Load",
    ]
    failure_modes = ["Timing violation", "Coverage gap", "Protocol mismatch",
                     "Register corruption", "Clock glitch", "Reset fault"]
    rows = []
    for unit_id in range(1, 31):
        board_rev = np.random.choice(["Rev C", "Rev D", "Rev E"],
                                     p=[0.2, 0.4, 0.4])
        batch = f"BATCH-{random.randint(8,15):03d}"
        date = datetime(2025, 1, 15) + timedelta(days=random.randint(0, 60))
        for suite in test_suites:
            base_pass = 0.72 + (0.02 if "Rev E" in board_rev else 0)
            passed = random.random() < base_pass
            coverage = round(random.uniform(85, 100) if passed else random.uniform(60, 89), 1)
            rows.append({
                "unit_id": f"UNIT-{unit_id:03d}",
                "board_rev": board_rev,
                "batch_id": batch,
                "test_suite": suite,
                "date": date.strftime("%Y-%m-%d"),
                "result": "PASS" if passed else "FAIL",
                "coverage_pct": coverage,
                "runtime_sec": round(random.uniform(12, 480), 1),
                "failure_mode": None if passed else random.choice(failure_modes),
                "seed": random.randint(100000, 999999),
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 5. DEPLOYMENT READINESS — Computed Summary
# ─────────────────────────────────────────────
def gen_readiness(fab_df, asm_df, test_df):
    rows = []
    for rev in ["Rev C", "Rev D", "Rev E"]:
        fab_row = fab_df[fab_df["revision"] == rev]
        fab_yield = fab_row["yield_pct"].values[0] if len(fab_row) else 0

        rev_tests = test_df[test_df["board_rev"] == rev]
        units = rev_tests["unit_id"].nunique()
        pass_rate = (rev_tests["result"] == "PASS").mean() * 100 if len(rev_tests) else 0
        avg_cov = rev_tests["coverage_pct"].mean() if len(rev_tests) else 0

        asm_defect = asm_df["defect_rate_pct"].mean()

        score = (fab_yield * 0.3 + pass_rate * 0.4 + avg_cov * 0.2 +
                 (100 - asm_defect * 10) * 0.1)

        rows.append({
            "revision": rev,
            "fab_yield_pct": round(fab_yield, 1),
            "asm_defect_rate_pct": round(asm_defect, 1),
            "test_pass_rate_pct": round(pass_rate, 1),
            "avg_coverage_pct": round(avg_cov, 1),
            "units_tested": units,
            "readiness_score": round(score, 1),
            "deployment_status": (
                "Ready" if score >= 85 else
                "Conditional" if score >= 70 else
                "Not Ready"
            ),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# WRITE TO SQLITE
# ─────────────────────────────────────────────
def main():
    print("Generating datasets...")
    bom_df   = gen_bom()
    fab_df   = gen_fabrication()
    asm_df   = gen_assembly()
    test_df  = gen_test_results()
    ready_df = gen_readiness(fab_df, asm_df, test_df)

    conn = sqlite3.connect(DB_PATH)
    bom_df.to_sql("bom",         conn, if_exists="replace", index=False)
    fab_df.to_sql("fabrication", conn, if_exists="replace", index=False)
    asm_df.to_sql("assembly",    conn, if_exists="replace", index=False)
    test_df.to_sql("test",       conn, if_exists="replace", index=False)
    ready_df.to_sql("readiness", conn, if_exists="replace", index=False)
    conn.close()

    # Also export CSVs for inspection
    csv_dir = os.path.join(os.path.dirname(__file__), "../data/synthetic")
    os.makedirs(csv_dir, exist_ok=True)
    bom_df.to_csv(f"{csv_dir}/bom.csv", index=False)
    fab_df.to_csv(f"{csv_dir}/fabrication.csv", index=False)
    asm_df.to_csv(f"{csv_dir}/assembly.csv", index=False)
    test_df.to_csv(f"{csv_dir}/test_results.csv", index=False)
    ready_df.to_csv(f"{csv_dir}/readiness.csv", index=False)

    print(f"✓ BOM:          {len(bom_df)} components")
    print(f"✓ Fabrication:  {len(fab_df)} revision records")
    print(f"✓ Assembly:     {len(asm_df)} defect log entries")
    print(f"✓ Test results: {len(test_df)} test runs")
    print(f"✓ Readiness:    {len(ready_df)} revision summaries")
    print(f"✓ Database:     {DB_PATH}")


if __name__ == "__main__":
    main()
