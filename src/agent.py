from typing import Optional
import random


class Agent:
    def act(self, current, state, graph):
        raise NotImplementedError()


class RandomAgent(Agent):
    def act(self, current, state, graph):
        neigh = graph.neighbors(current)
        if not neigh:
            return None
        return random.choice([n for n, d in neigh])


class GreedyAgent(Agent):
    def __init__(self, simulator, greedy_factor: float = 1.0):
        self.sim = simulator
        self.greedy_factor = greedy_factor

    def act(self, current, state, graph):
        # choose neighbor maximizing reward / cost
        best = None
        best_val = -float('inf')
        for n, d in graph.neighbors(current):
            cost = self.sim.move_cost(d)
            reward = self.sim.node_sustainability(n)
            val = (reward ** self.greedy_factor) / (cost + 1e-6)
            if val > best_val:
                best_val = val
                best = n
        return best
