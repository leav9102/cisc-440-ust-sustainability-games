# CISC 440 — UST Campus Sustainability Games

AI-based sustainability games on a simplified University of St. Thomas (St. Paul) campus graph, using official course datasets and Monte Carlo simulation under uncertainty.

## Team

| Name | Role | GitHub |
|------|------|--------|
| _Add member_ | | |
| _Add member_ | | |

## Project goals

1. Build 1–2 AI-based sustainability games using real UST data  
2. Test the system under uncertainty with Monte Carlo simulation  
3. Connect the project to modern AI research (see `report/`)

## Repository layout

```
├── data/          # CSV/XLSX from Canvas (not committed — see data/README.md)
├── src/           # Game logic, agents, Monte Carlo
├── output/        # Plots and simulation results (generated)
├── report/        # Final write-up and design notes
└── PROJECT_START.md
```

## Setup

### 1. Clone this repo

```bash
git clone https://github.com/YOUR_ORG/cisc-440-final-project.git
cd cisc-440-final-project
```

### 2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Download course data

Place all Canvas files in `data/`. See [data/README.md](data/README.md) for the file list.

### 4. Run (after you implement)

```bash
python src/main.py
```

## Data sources

All datasets are provided on Canvas for CISC 440. Nodes and edges define the campus graph; energy, resources, and sustainability files inform scores and costs.

## Academic integrity

Course AI policy: AI may assist with clarity and organization, not replace your implementation or understanding. Document design decisions in `report/design_notes.md`.

## License

Course project — University of St. Thomas. Do not redistribute instructor datasets outside the course.
