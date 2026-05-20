import os
from typing import Dict, List, Tuple, Set, Optional
import pandas as pd


class DataLoader:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def _path(self, name: str) -> str:
        return os.path.join(self.data_dir, name)

    def load_nodes(self) -> pd.DataFrame:
        return pd.read_csv(self._path('ust_selected_game_nodes.csv'))

    def load_edges(self) -> pd.DataFrame:
        return pd.read_csv(self._path('ust_building_edges.csv'))

    def load_coordinates(self) -> pd.DataFrame:
        return pd.read_csv(self._path('ust_building_coordinates.csv'))

    def load_distance_matrix(self) -> pd.DataFrame:
        return pd.read_csv(self._path('ust_distance_matrix.csv'))

    def load_energy_assets(self) -> pd.DataFrame:
        return pd.read_csv(self._path('ust_energy_assets.csv'))


class CampusGraph:
    def __init__(self, nodes_df: pd.DataFrame, edges_df: pd.DataFrame):
        # Expect edges_df to have columns: source, target, distance (or weight)
        self.nodes_df = nodes_df
        self.edges_df = edges_df
        self.adj: Dict[str, List[Tuple[str, float]]] = {}
        self._build()

    def _build(self):
        # Normalize expected column names
        src_col = None
        tgt_col = None
        dist_col = None
        for c in self.edges_df.columns:
            cl = c.lower()
            if 'from' in cl or 'source' in cl or 'a' == cl:
                src_col = c
            if 'to' in cl or 'target' in cl or 'b' == cl:
                tgt_col = c
            if 'dist' in cl or 'distance' in cl or 'length' in cl:
                dist_col = c
        if src_col is None or tgt_col is None:
            # fallback: assume first two columns
            src_col = self.edges_df.columns[0]
            tgt_col = self.edges_df.columns[1]
        if dist_col is None:
            # fallback: no distances, use 1.0
            self.edges_df['__dist'] = 1.0
            dist_col = '__dist'

        for _, r in self.edges_df.iterrows():
            a = str(r[src_col])
            b = str(r[tgt_col])
            d = float(r[dist_col])
            self.adj.setdefault(a, []).append((b, d))
            self.adj.setdefault(b, []).append((a, d))

    def neighbors(self, node: str) -> List[Tuple[str, float]]:
        return self.adj.get(node, [])


class GameState:
    def __init__(self, start_node: str, energy: float, max_steps: int = 100):
        self.current = start_node
        self.energy = energy
        self.max_steps = max_steps
        self.steps = 0
        self.visited: Set[str] = {start_node}
        self.score = 0.0
        self.done = False

    def step_move(self, target: str, cost: float, reward: float):
        if self.done:
            return
        # apply move
        self.current = target
        self.steps += 1
        self.energy -= cost
        self.score += reward
        self.visited.add(target)
        if self.energy <= 0 or self.steps >= self.max_steps:
            self.done = True


class GameSimulator:
    def __init__(self, graph: CampusGraph, nodes_df: pd.DataFrame, energy_per_unit: float = 1.0,
                 sustainability_col: Optional[str] = None):
        self.graph = graph
        self.nodes_df = nodes_df
        self.energy_per_unit = energy_per_unit
        # detect sustainability column if not provided
        self.sustain_col = sustainability_col
        if self.sustain_col is None:
            for c in nodes_df.columns:
                if 'sustain' in c.lower() or 'score' in c.lower():
                    self.sustain_col = c
                    break

    def node_sustainability(self, node: str) -> float:
        # match node against nodes_df by name-like column
        for col in self.nodes_df.columns:
            if 'name' in col.lower() or 'id' in col.lower():
                matches = self.nodes_df[self.nodes_df[col].astype(str) == str(node)]
                if not matches.empty:
                    if self.sustain_col and self.sustain_col in self.nodes_df.columns:
                        return float(matches.iloc[0][self.sustain_col])
                    return 1.0
        return 1.0

    def move_cost(self, distance: float) -> float:
        return distance * self.energy_per_unit

    def run_episode(self, start: str, agent, max_steps: int = 100, start_energy: float = 100.0,
                    verbose: bool = False) -> GameState:
        state = GameState(start, start_energy, max_steps)
        while not state.done:
            action = agent.act(state.current, state, self.graph)
            if action is None:
                state.done = True
                break
            # action expected to be target node string
            # find distance
            neigh = {n: d for n, d in self.graph.neighbors(state.current)}
            if action not in neigh:
                # invalid move: end episode
                state.done = True
                break
            dist = neigh[action]
            cost = self.move_cost(dist)
            reward = self.node_sustainability(action)
            state.step_move(action, cost, reward)
            if verbose:
                print(f"Moved to {action} cost={cost:.2f} reward={reward:.2f} energy={state.energy:.2f}")
        return state
