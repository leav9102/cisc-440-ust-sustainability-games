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
| **State** |  |
| **Actions** |  |
| **Reward / cost** |  |
| **Terminal condition** |  |
| **AI method** | |
| **Data columns used** |  |

## Monte Carlo

- **What is uncertain:** Movement cost and event noise are added into each AI simulation of the game (e.g. ±10% cost noise, occasional building closure event simulated). The code's Monte Carlo mode repeats route planning to capture variability in the results.
- **Distribution / parameters:** Suggest using ±10% variability noise on edge distances (normal or uniform) and a 10–20% chance a random node is unavailable per run.
- **Number of runs:** Default is 100, recommended is 500 for final analysis.
- **Metrics reported:** Mean, standard deviation, min, max route cost; % runs that complete with non-negative energy; histogram saved to `output/`.

## Research connection

- **Concept from course:** Heuristic search / A* (state, action, cost, heuristic) and Monte Carlo evaluation of policy robustness under uncertainty.
- **Reference:** Russell & Norvig, "Artificial Intelligence: A Modern Approach" (A* and heuristic search), or course lecture notes on search and Monte Carlo simulation.