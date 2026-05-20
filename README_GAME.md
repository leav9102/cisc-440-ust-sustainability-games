# Campus Sustainability Patrol — Quick Run

Requirements (install into your Python environment):

```bash
pip install -r requirements.txt
```

Run a search-based sustainable route between two buildings:

```bash
python3 src/run_game.py --data data --mode search --start "Anderson Student Center" --goal "Frey Residence Hall"
```

Solve the CSP-based resource placement problem:

```bash
python3 src/run_game.py --data data --mode csp
```

Run the minimax sustainability showdown (interactive or auto mode):

```bash
python3 src/run_game.py --data data --mode showdown
```

Run Monte Carlo route cost simulation:

```bash
python3 src/run_game.py --data data --mode mc --runs 100
```

Use `--auto` to skip trivia prompts and assume correct answers.

This system uses the campus graph from `ust_building_edges.csv`, location metadata from `ust_selected_game_nodes.csv`, sustainability assets from `ust_energy_assets.csv`, and trivia content from `Sustainability Trivia Game 2026.docx`.
