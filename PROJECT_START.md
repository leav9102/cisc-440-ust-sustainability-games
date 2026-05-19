# CISC 440 Final Project — Start Here

Use this as your checklist. Do the steps in order; do not jump to "full game" until Step 4 is done.

---

## Step 0 — Today (30 minutes)

1. Create folders:
   ```
   CISC 440 Final Project/
     data/          ← all CSV/XLSX from Canvas
     src/           ← your Python code (you write this)
     output/        ← plots, Monte Carlo results
     report/        ← final write-up
   ```
2. Download from Canvas into `data/`:
   - ust_selected_game_nodes.csv
   - ust_building_edges.csv
   - ust_building_coordinates.csv
   - ust_distance_matrix.csv
   - ust_energy_assets.csv
   - ust_campus_resources.csv
   - ust_sustainability_factors.csv
   - ust_sustainability_data_pack.xlsx (optional overview)
   - ust_campus_map_plot.py (reference only at first)
3. Open the three files in Excel or Google Sheets and answer (on paper):
   - How many nodes? What are their names?
   - How many edges? Are distances in feet/meters?
   - What columns exist in energy_assets and sustainability_factors?

---

## Step 1 — Pick ONE game (keep it simple)

**Recommended starter: "Campus Sustainability Patrol"**

- **You** are an AI agent (or you simulate one) on the campus graph.
- **Goal:** Maximize sustainability score before running out of energy/steps.
- **Move:** Only along edges in `ust_building_edges.csv`.
- **Costs/rewards** come from real columns (you choose which columns in your design doc).

Write this in `report/design_notes.md` (create when ready):

| Design piece | Your choice (fill in) |
|--------------|----------------------|
| State | e.g. current node, remaining energy, visited set |
| Actions | move to neighbor node |
| Reward | +sustainability factor at node, −energy cost, −distance penalty |
| Terminal | out of steps, or reached target, or all key nodes visited |
| AI method | e.g. greedy heuristic, A*, or Q-learning (pick one you can explain) |

**Second game (optional later):** Trivia at nodes using the Sustainability Trivia doc — only add after Game 1 runs.

---

## Step 2 — Understand the graph (before any AI)

You must be able to draw the graph on paper:

- Nodes = rows in `ust_selected_game_nodes.csv`
- Edge A→B exists only if listed in `ust_building_edges.csv`

Deliverable for yourself: a sketch with 10–15 nodes and labeled edges. If `ust_campus_map_plot.py` works after you have data, use it to sanity-check layout.

---

## Step 3 — Map data → numbers (critical for grading)

For each number in your game, write **which file and column** it came from.

Example (you must verify against your files):

| Game concept | Data source | Column (verify!) |
|--------------|-------------|------------------|
| High visit cost | ust_energy_assets.csv | (e.g. annual kWh or similar) |
| Recycling bonus | ust_campus_resources.csv | (resource type / score) |
| Sustainability weight | ust_sustainability_factors.csv | (factor name / value) |
| Walk cost | ust_distance_matrix.csv or edges | distance |

If a column is missing or unclear, document that and use a simple transform you define (e.g. normalize to 0–1) — and explain why in the report.

---

## Step 4 — Build in thin slices (you code each slice)

| Order | What to build | Done when |
|-------|---------------|-----------|
| 4a | Load CSVs, print node list | You see 10–15 nodes in terminal |
| 4b | Build adjacency dict from edges | You can list neighbors of any node |
| 4c | Manual play: you type node names to move | Path respects edges only |
| 4d | Scoring function using your column mapping | Score changes when you visit nodes |
| 4e | One AI policy (start with greedy: pick neighbor with best score/distance) | Agent completes one episode |
| 4f | Monte Carlo: loop 500–1000 episodes with random noise | You have mean, std, success % |
| 4g | Plot + short analysis | Figure in `output/` |

Do **not** skip 4a–4c. Most "I'm stuck" feelings come from trying to build the whole game at once.

---

## Step 5 — Monte Carlo (what the course wants)

**Uncertainty** = something random each run, for example:

- ±10% on energy cost
- Random "event" (e.g. 20% chance a building is closed)
- Noisy sustainability factor

**Procedure:**

1. Fix your agent/policy.
2. Run the same scenario N times (e.g. N = 1000).
3. Record total score (or success/fail) each time.
4. Report: mean, standard deviation, % runs above a threshold.

You are testing **robustness under uncertainty**, not just one lucky run.

---

## Step 6 — Research connection (1 paragraph in report)

Pick **one** idea from class and tie it to your game, e.g.:

- Markov decision process (state, action, reward, transition)
- Heuristic search (A* with sustainability heuristic)
- Reinforcement learning (Q-table on small graph)
- Multi-objective tradeoff (energy vs. recycling)

Cite one paper or textbook section if required by the rubric.

---

## Step 7 — Report outline (write early, fill as you go)

1. Introduction — UST sustainability game on campus graph  
2. Data — which files, which columns, how normalized  
3. Game design — state, actions, rewards, constraints  
4. AI approach — algorithm and why it fits  
5. Monte Carlo — what is uncertain, N runs, results  
6. Results — tables/plots  
7. Limitations — dataset simplifications  
8. Conclusion — what you learned  

---

## If you feel stuck

| Feeling | Next action |
|---------|-------------|
| "Too big" | Only do Step 4a today |
| "Don't know AI" | Use greedy neighbor choice first; upgrade later |
| "Don't know Python graphs" | adjacency dict: `{node: [neighbor1, neighbor2]}` |
| "Monte Carlo confusing" | `for i in range(1000): score = run_episode(random_noise)` |

---

## Academic integrity reminder

You must implement and explain your code. AI tools may help clarify ideas and polish writing — not replace your implementation. Keep a log of **your** design decisions in `report/design_notes.md`.
