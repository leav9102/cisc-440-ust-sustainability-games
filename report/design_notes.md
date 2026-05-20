# Design notes

Fill this in as you build. Graders (and you, at demo time) should be able to trace every number to a data file.

## Game 1: Campus Sustainability Patrol

| Piece | Your definition |
|-------|-----------------|
| **State** | `current_node` (building_name; string), `remaining_energy` (float), `visited` (set of node names), `steps` (int), `score` (float) |
| **Actions** | Move along an edge to a neighboring building in the graph. Can also end turn if nothing is better at the moment. |
| **Reward / cost** | Reward is sustainability score at the node computed from `ust_selected_game_nodes.csv`. Cost is movement cost which is equal to edge distance (from `ust_building_edges.csv` `Distance` column, or `ust_distance_matrix.csv` when available) multiplied by energy-per-unit (default 1.0), and node penalty (negative). |
| **Terminal condition** | `remaining_energy <= 0` or `steps >= max_steps`, all key nodes reached, or target was reached. |
| **AI method** | Primarily A*-style route planning (`SearchGame.plan_route`) using edge cost = distance*100 + node penalty. Additionally, greedy heuristic (`GreedyAgent`) and Monte Carlo evaluation. |
| **Data columns used** | See mapping table below. |

## Game 2 (optional)

| Piece | Your definition |
|-------|-----------------|
| **State** | (optional) placements map, penalties, placements_left |
| **Actions** | (optional) place `recycling`/`compost` at candidate nodes or trigger penalty actions (opponent) |
| **Reward / cost** | (optional) placement value defined by `ResourceCSP` / `MinimaxShowdown` scoring functions; influenced by node scores from Game 1 data mappings |
| **Terminal condition** | (optional) placements exhausted or fixed depth minimax reached |
| **AI method** | (optional) CSP backtracking for placements; Minimax with alpha-beta for showdown decisions |
| **Data columns used** | (optional) same node metadata files as Game 1 plus `ust_campus_resources.csv` if you map resource availability |

## Monte Carlo

- **What is uncertain:** Movement cost and event noise (e.g. ±10% cost noise, occasional building closure event). The code's Monte Carlo mode repeats route planning to capture variability.
- **Distribution / parameters:** Suggest using ±10% multiplicative noise on edge distances (normal or uniform) and a 10–20% chance a random node is unavailable per run.
- **Number of runs:** Default `100` (CLI `--runs`), recommended `>=500` for final analysis.
- **Metrics reported:** Mean, standard deviation, min, max route cost; % runs that complete with non-negative energy; histogram saved to `output/`.

## Research connection

- **Concept from course:** Heuristic search / A* (state, action, cost, heuristic) and Monte Carlo evaluation of policy robustness under uncertainty.
- **Reference:** Russell & Norvig, "Artificial Intelligence: A Modern Approach" (A* and heuristic search), or course lecture notes on search and Monte Carlo simulation.

---

### Data-to-column mapping (explicit)

| Game concept | File | Column(s) / notes |
|--------------|------|--------------------|
| Node identity | `ust_selected_game_nodes.csv` | `building_name` (primary display key), `code` (optional alias) |
| Node metadata for scoring | `ust_selected_game_nodes.csv` | `sustainability_relevance`, `category` (used to derive keywords like 'solar', 'compost', 'recycling', 'LEED' levels) |
| Edge connectivity & walk cost | `ust_building_edges.csv` | `Source` / `Target` (or similar first two cols), `Distance` (used as base movement cost). When present, `ust_distance_matrix.csv` is used for A* heuristic lookups. |
| Energy / assets influence | `ust_energy_assets.csv` | `location_name`, `asset_type` (e.g. `leed_building`, `solar_asset`, `microgrid_asset` — these increment node score in code) |
| Sustainability factors (optional) | `ust_sustainability_factors.csv` | Extra factors you may map into node scoring if desired (not required by current code) |
| Trivia / vocabulary | `Sustainability Trivia Game 2026.docx` and `sustainability_words.txt` | Trivia questions (DOCX) and quick vocab prompts (`sustainability_words.txt`) used by `TriviaEngine` to modify costs/bonuses. |

---

### Notes / next steps to align with grading rubric

- Fill the `Data columns used` table in the Game 1 section of this file exactly with column names as they appear in your copy of `ust_selected_game_nodes.csv` and `ust_building_edges.csv` (open CSV and copy headers).  
- Implement explicit Monte Carlo noise injection in `SearchGame`/`run_monte_carlo` (±10% distance noise and occasional closures) if you want the grader to see uncertainty modeling (recommended).  
- Mark `Game 1: Campus Sustainability Patrol` as the primary game in your report and treat `csp`/`showdown` as optional extras.

