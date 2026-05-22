import csv, heapq, math, os, random, statistics

try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_PLT = True
except ImportError:
    HAS_PLT = False

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT  = os.path.join(os.path.dirname(__file__), "output")
RUNS = 500
SEED = 25

def build_graph():
    def load(name):
        with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    # Adjacency list from edges CSV
    adj = {}
    for r in load("ust_game_subset_15edges.csv"):
        s, t, d = r["Source"].strip(), r["Target"].strip(), float(r["Distance"])
        adj.setdefault(s, []).append((t, d))
        adj.setdefault(t, []).append((s, d))

    scores = {}
    for r in load("ust_game_subset_15nodes.csv"):
        name = r["building_name"].strip()
        txt  = (r.get("sustainability_relevance","") + " " + r.get("category","")).lower()
        sc   = 1.0
        if "leed platinum" in txt: sc += 1.5
        elif "leed gold"   in txt: sc += 1.0
        elif "leed silver" in txt: sc += 0.6
        if "solar"         in txt: sc += 0.7
        if "recycling"     in txt or "compost" in txt: sc += 0.5
        if "microgrid"     in txt: sc += 0.8
        if "bike"          in txt or "ev" in txt: sc += 0.4
        if "parking"       in r.get("category","").lower(): sc -= 0.5
        scores[name] = max(0.5, sc)

    # penalty = 5 - score  (high score → low penalty → sustainable route prefers it)
    penalties = {n: max(0.1, 5.0 - s) for n, s in scores.items()}
    return list(adj), adj, scores, penalties

def find_path(adj, start, goal, edge_cost_fn):
    """Dijkstra with a pluggable edge-cost function."""
    heap = [(0.0, start)]
    cost = {start: 0.0}
    prev = {start: None}
    while heap:
        c, u = heapq.heappop(heap)
        if u == goal: break
        for v, d in adj.get(u, []):
            nc = c + edge_cost_fn(u, v, d)
            if nc < cost.get(v, math.inf):
                cost[v] = nc; prev[v] = u
                heapq.heappush(heap, (nc, v))
    if goal not in prev: return None
    path, n = [], goal
    while n: path.append(n); n = prev[n]
    return path[::-1]

def make_uncertainty(adj, nodes, scores):
    travel = {(u,v): random.uniform(0.9, 1.8) for u, nbrs in adj.items() for v,_ in nbrs}
    energy = {}
    for n in nodes:
        sc = scores.get(n, 1.0)
        lo, hi = (0.85,1.20) if sc>=3 else (0.82,1.35) if sc>=1.5 else (0.80,1.50)
        energy[n] = random.uniform(lo, hi)
    return travel, energy

def run_simulation():
    nodes, adj, scores, penalties = build_graph()
    random.seed(SEED)

    costs_s, costs_d = [], []  
    gains_s, gains_d = [], []  
    wins = {"s": 0, "d": 0, "tie": 0}

    for _ in range(RUNS):
        start, goal = random.sample(nodes, 2)
        travel, energy = make_uncertainty(adj, nodes, scores)

        # Strategy 1: Sustainable — cost includes sustainability penalty
        def green_cost(u, v, d):
            return d * 100 * travel.get((u,v), 1.0) + penalties.get(v, 2.0) * energy.get(v, 1.0)

        # Strategy 2: Shortest — cost is distance only
        def short_cost(u, v, d):
            return d * 100 * travel.get((u,v), 1.0)

        path_s = find_path(adj, start, goal, green_cost)
        path_d = find_path(adj, start, goal, short_cost)
        if not path_s or not path_d: continue

        def eval_path(path):
            cost = 0.0
            for i in range(len(path)-1):
                u, v = path[i], path[i+1]
                d = next((x for n,x in adj.get(u,[]) if n==v), None)
                if d is None: return math.inf
                cost += d*100*travel.get((u,v),1.0) + penalties.get(v,2.0)*energy.get(v,1.0)
            return cost

        cs, cd = eval_path(path_s), eval_path(path_d)
        if cs == math.inf or cd == math.inf: continue

        costs_s.append(cs); costs_d.append(cd)
        gains_s.append(sum(scores.get(n,1.0) for n in path_s))
        gains_d.append(sum(scores.get(n,1.0) for n in path_d))

        if   cs < cd - 0.005: wins["s"] += 1
        elif cd < cs - 0.005: wins["d"] += 1
        else:                  wins["tie"] += 1

    return costs_s, costs_d, gains_s, gains_d, wins, scores, penalties



def report(costs_s, costs_d, gains_s, gains_d, wins, scores, penalties):
    n = len(costs_s)
    avg_cs, avg_cd = statistics.mean(costs_s), statistics.mean(costs_d)
    avg_gs, avg_gd = statistics.mean(gains_s), statistics.mean(gains_d)

    print(f"""
  RESULTS ({n} runs)
    {'Metric':<26} {'Sustainable':>11}  {'Shortest':>10}
    {'-'*50}
    {'Avg realized cost':<26} {avg_cs:>11.3f}  {avg_cd:>10.3f}
    {'Best cost (min)':<26} {min(costs_s):>11.3f}  {min(costs_d):>10.3f}
    {'Worst cost (max)':<26} {max(costs_s):>11.3f}  {max(costs_d):>10.3f}
    {'Std deviation':<26} {statistics.stdev(costs_s):>11.3f}  {statistics.stdev(costs_d):>10.3f}
    {'Avg sustainability score':<26} {avg_gs:>11.3f}  {avg_gd:>10.3f}

  Head-to-head (lower realized cost wins):
    Sustainable wins : {wins['s']:>4}  ({100*wins['s']/n:.1f}%)
    Shortest wins    : {wins['d']:>4}  ({100*wins['d']/n:.1f}%)
    Ties             : {wins['tie']:>4}  ({100*wins['tie']/n:.1f}%)
""")
    print("="*58)


def plot(costs_s, costs_d, gains_s, gains_d):
    if not HAS_PLT: return
    os.makedirs(OUT, exist_ok=True)
    G, B = "#2e8b57", "#4169e1"

    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"UST Monte Carlo: Sustainable vs Shortest Route ({RUNS} runs)",
                 fontweight="bold")

    ax[0].hist(costs_s, bins=30, alpha=0.7, color=G, label=f"Sustainable (avg={statistics.mean(costs_s):.2f})")
    ax[0].hist(costs_d, bins=30, alpha=0.7, color=B, label=f"Shortest    (avg={statistics.mean(costs_d):.2f})")
    ax[0].axvline(statistics.mean(costs_s), color="darkgreen", linestyle="--")
    ax[0].axvline(statistics.mean(costs_d), color="darkblue",  linestyle="--")
    ax[0].set(xlabel="Realized Cost", ylabel="Frequency", title="Cost Distribution")
    ax[0].legend()

    ax[1].hist(gains_s, bins=20, alpha=0.7, color=G, label=f"Sustainable (avg={statistics.mean(gains_s):.2f})")
    ax[1].hist(gains_d, bins=20, alpha=0.7, color=B, label=f"Shortest    (avg={statistics.mean(gains_d):.2f})")
    ax[1].axvline(statistics.mean(gains_s), color="darkgreen", linestyle="--")
    ax[1].axvline(statistics.mean(gains_d), color="darkblue",  linestyle="--")
    ax[1].set(xlabel="Sustainability Score", ylabel="Frequency", title="Sustainability Accumulated")
    ax[1].legend()

    plt.tight_layout()
    out = os.path.join(OUT, "mc_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Plot saved → {out}")


if __name__ == "__main__":
    print(f"Running {RUNS} Monte Carlo simulations...")
    costs_s, costs_d, gains_s, gains_d, wins, scores, penalties = run_simulation()
    print(f"Done — {len(costs_s)} valid runs.\n")
    report(costs_s, costs_d, gains_s, gains_d, wins, scores, penalties)
    plot(costs_s, costs_d, gains_s, gains_d)
