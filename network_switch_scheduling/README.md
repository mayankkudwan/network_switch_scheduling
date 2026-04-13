# Network Switch Scheduling Algorithms
### Assignment: Evaluating FIFO, VOQ-Optimal, and iSLIP on a 3×3 Crossbar Switch

---

## 📁 Repository Structure

```
network-switch-scheduling/
│
├── switch_simulation.py       ← Main simulation code (all 3 algorithms + graphs)
├── Switch_Scheduling_Report.docx  ← Full lab report
├── switch_graphs.png          ← Output graphs (generated on run)
└── README.md                  ← This file
```

---

## ⚙️ Requirements

Make sure you have **Python 3.7+** installed.  
Check by running:
```bash
python --version
```

Install the only required library:
```bash
pip install matplotlib
```

No other libraries needed — `collections`, `itertools`, `io`, `os`, `sys` are all built into Python.

---

## ▶️ How to Run

### Google Colab
1. Upload `switch_simulation.py` to Colab
2. In a new cell, run:
```python
exec(open('switch_simulation.py').read())
```
3. The graphs display **inline** in the notebook

---

## 📊 What the Code Does

The simulation runs in 4 parts:

| Part | Description |
|------|-------------|
| **Part 1** | FIFO queuing with Head-of-Line blocking detection |
| **Part 2** | VOQ with exhaustive optimal matching |
| **Part 3** | VOQ with iSLIP scheduling (3 iterations per slot) |
| **Part 4** | Generates 2 comparison graphs |

---

## ✅ Expected Output

After running, you will see a step-by-step log in the terminal like:

```
============================================================
PART 1: FIFO Queue with HoL Blocking
============================================================

--- t=0 | Backlog(start)=5 ---
  SEND: p1 | I0 -> O0
  [HoL BLOCKED] p3 at I1 wants O0 but lost to I0
  [HoL BLOCKING] p4 (I1, wants O2 [IDLE]) blocked behind p3
...

✅ FIFO Total Service Time: 11 time slots

============================================================
PART 2: VOQ - Optimal Exhaustive Search
============================================================
...
✅ VOQ-Optimal Total Service Time: 7 time slots

============================================================
PART 3: VOQ with iSLIP (3 iterations)
============================================================
...
✅ iSLIP Total Service Time: 8 time slots

============================================================
SUMMARY
============================================================
  FIFO Total Service Time:        11
  VOQ-Optimal Total Service Time: 7
  iSLIP Total Service Time:       8
```

At the end, **two graphs appear**:
- **Bar Chart** — Total service time comparison
- **Line Graph** — Backlog (packets remaining) over time for all 3 algorithms

---

## 📈 Results Summary

| Algorithm | Total Service Time | Peak Backlog |
|---|---|---|
| FIFO (Head-of-Line Blocking) | **11 time slots** | 6 |
| VOQ — Optimal | **7 time slots** | 2 |
| VOQ — iSLIP (3 iterations) | **8 time slots** | 4 |

---

**Graph doesn't appear (running as .py script)**  
The graph is also saved as `switch_graphs.png` in the same folder. 
Open it with any image viewer.


## 📝 Algorithm Overview

### FIFO
Each input has one shared queue. Only the head packet can be sent. Lower-numbered input wins ties. Suffers from Head-of-Line (HoL) blocking.

### VOQ — Optimal
Each input has 3 separate queues (one per destination). Exhaustive search finds the maximum bipartite matching every slot. No HoL blocking. Theoretically optimal but not practical for hardware.

### iSLIP (3 iterations)
Uses VOQ architecture with round-robin Grant and Accept arbiters. Each iteration runs Request → Grant → Accept. Pointers advance only on accept, ensuring long-term fairness. Near-optimal and hardware-implementable.
