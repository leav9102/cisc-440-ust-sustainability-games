import csv
import heapq
import math
import os
import random
from typing import Dict, List, Optional, Tuple

try:
    from docx import Document
except ImportError:
    Document = None


def normalize_name(name: str) -> str:
    return ''.join(ch.lower() for ch in str(name) if ch.isalnum())


class DataLoader:
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir

    def load_nodes(self) -> List[Dict[str, str]]:
        path = os.path.join(self.data_dir, 'ust_selected_game_nodes.csv')
        with open(path, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def load_edges(self) -> List[Dict[str, str]]:
        path = os.path.join(self.data_dir, 'ust_building_edges.csv')
        with open(path, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def load_distance_matrix(self) -> Dict[Tuple[str, str], float]:
        path = os.path.join(self.data_dir, 'ust_distance_matrix.csv')
        matrix: Dict[Tuple[str, str], float] = {}
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows:
            return matrix
        headers = rows[0][1:]
        for row in rows[1:]:
            row_name = row[0]
            for col_name, value in zip(headers, row[1:]):
                if value.strip() == '':
                    continue
                try:
                    dist = float(value)
                except ValueError:
                    continue
                matrix[(row_name.strip(), col_name.strip())] = dist
                matrix[(col_name.strip(), row_name.strip())] = dist
        return matrix

    def load_energy_assets(self) -> List[Dict[str, str]]:
        path = os.path.join(self.data_dir, 'ust_energy_assets.csv')
        with open(path, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def load_sustainability_factors(self) -> List[Dict[str, str]]:
        path = os.path.join(self.data_dir, 'ust_sustainability_factors.csv')
        with open(path, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def load_vocabulary(self) -> List[str]:
        path = os.path.join(self.data_dir, 'sustainability_words.txt')
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def load_trivia(self) -> List[Dict[str, str]]:
        questions: List[Dict[str, str]] = []
        path = os.path.join(self.data_dir, 'Sustainability Trivia Game 2026.docx')
        if Document is None or not os.path.exists(path):
            return questions
        doc = Document(path)
        for table in doc.tables:
            headers = [cell.text.strip() for cell in table.rows[0].cells]
            for row in table.rows[1:]:
                row_text = [cell.text.strip() for cell in row.cells]
                if len(row_text) < 3:
                    continue
                topic, mc_text, tf_text = row_text[:3]
                if 'Question:' in mc_text and 'Answer:' in mc_text:
                    question, answer = self._parse_question(mc_text)
                    if question:
                        questions.append({
                            'topic': topic,
                            'text': question,
                            'answer': answer,
                            'type': 'mc',
                        })
                if 'Statement:' in tf_text and 'Answer:' in tf_text:
                    statement, answer = self._parse_question(tf_text, prefix='Statement:')
                    if statement:
                        questions.append({
                            'topic': topic,
                            'text': statement,
                            'answer': answer,
                            'type': 'tf',
                        })
        return questions

    @staticmethod
    def _parse_question(text: str, prefix: str = 'Question:') -> Tuple[Optional[str], Optional[str]]:
        parts = text.split('Answer:')
        if len(parts) != 2:
            return None, None
        question = parts[0].replace(prefix, '').strip()
        answer = parts[1].strip().split()[0]
        return question, answer


class CampusGraph:
    def __init__(self, data_dir: str = 'data'):
        self.loader = DataLoader(data_dir)
        self.nodes = self.loader.load_nodes()
        self.edges = self.loader.load_edges()
        self.distances = self.loader.load_distance_matrix()
        self.energy_assets = self.loader.load_energy_assets()
        self.sustainability_factors = self.loader.load_sustainability_factors()
        self.vocabulary = self.loader.load_vocabulary()
        self.trivia_questions = self.loader.load_trivia()
        self.alias_map: Dict[str, str] = {}
        self.all_nodes: Dict[str, Dict[str, str]] = {}
        self.adj: Dict[str, List[Tuple[str, float]]] = {}
        self.node_scores: Dict[str, float] = {}
        self.node_penalties: Dict[str, float] = {}
        self._build()

    def _add_alias(self, alias: str, full_name: str) -> None:
        key = normalize_name(alias)
        if key and key not in self.alias_map:
            self.alias_map[key] = full_name

    def _build(self) -> None:
        for row in self.nodes:
            full_name = row['building_name'].strip()
            if not full_name:
                continue
            self.all_nodes[full_name] = row
            self._add_alias(full_name, full_name)
            self._add_alias(row.get('code', ''), full_name)
            self._add_alias(full_name.replace(' ', ''), full_name)
            for token in full_name.replace('/', ' ').replace('-', ' ').split():
                self._add_alias(token, full_name)
            tokens = [token for token in full_name.replace('/', ' ').replace('-', ' ').split() if token]
            if len(tokens) > 1:
                self._add_alias(''.join(tokens), full_name)
                short_tokens = [t for t in tokens if t.lower() not in {'residence', 'student', 'educational', 'center', 'building'}]
                if len(short_tokens) > 1:
                    self._add_alias(''.join(short_tokens), full_name)
                if short_tokens:
                    self._add_alias(short_tokens[-1], full_name)
            self._add_alias(full_name.replace('Building', '').replace('Hall', '').strip(), full_name)

        for row in self.energy_assets:
            location = row.get('location_name', '').strip()
            if not location:
                continue
            if normalize_name(location) not in self.alias_map:
                self._add_alias(location, location)

        for row in self.edges:
            source = self.resolve_name(row.get('Source', ''))
            target = self.resolve_name(row.get('Target', ''))
            if source is None:
                source = row.get('Source', '').strip()
            if target is None:
                target = row.get('Target', '').strip()
            try:
                dist = float(row.get('Distance', '1.0'))
            except ValueError:
                dist = 1.0
            self.adj.setdefault(source, []).append((target, dist))
            self.adj.setdefault(target, []).append((source, dist))

        for name in list(self.adj):
            if name not in self.all_nodes:
                self.all_nodes[name] = {
                    'building_name': name,
                    'code': normalize_name(name),
                    'category': 'unknown',
                    'sustainability_relevance': '',
                    'source_url': '',
                    'status': '',
                }
        self._compute_scores()

    def resolve_name(self, alias: str) -> Optional[str]:
        if alias is None:
            return None
        key = normalize_name(alias)
        if key in self.alias_map:
            return self.alias_map[key]
        return None

    def neighbors(self, node_name: str) -> List[Tuple[str, float]]:
        return self.adj.get(node_name, [])

    def heuristic(self, current: str, goal: str) -> float:
        if (current, goal) in self.distances:
            return self.distances[(current, goal)] * 100.0
        return 0.0

    def _compute_scores(self) -> None:
        asset_map: Dict[str, List[Dict[str, str]]] = {}
        for row in self.energy_assets:
            location = row.get('location_name', '').strip()
            if location:
                canonical = self.resolve_name(location) or location
                asset_map.setdefault(canonical, []).append(row)

        for name, info in self.all_nodes.items():
            score = 1.0
            text = ' '.join([str(info.get('sustainability_relevance', '')), str(info.get('category', ''))]).lower()
            if 'leed platinum' in text:
                score += 1.5
            elif 'leed gold' in text:
                score += 1.0
            elif 'leed silver' in text:
                score += 0.6
            if 'solar' in text:
                score += 0.7
            if 'compost' in text or 'recycling' in text:
                score += 0.5
            if 'microgrid' in text or 'energy research' in text:
                score += 0.8
            if 'green building' in text or 'bike' in text or 'ev' in text:
                score += 0.4
            for asset in asset_map.get(name, []):
                asset_type = asset.get('asset_type', '').lower()
                if asset_type == 'leed_building':
                    score += 0.8
                elif asset_type == 'solar_asset':
                    score += 0.7
                elif asset_type == 'microgrid_asset':
                    score += 0.7
            if 'parking' in str(info.get('category', '')).lower():
                score -= 0.5
            self.node_scores[name] = max(0.5, score)
            self.node_penalties[name] = max(0.1, 5.0 - self.node_scores[name])

    def get_node_score(self, name: str) -> float:
        return self.node_scores.get(name, 1.0)

    def get_node_penalty(self, name: str) -> float:
        return self.node_penalties.get(name, 2.0)

    def get_trivia_question(self) -> Optional[Dict[str, str]]:
        if self.trivia_questions:
            return random.choice(self.trivia_questions)
        return None

    def get_vocab_term(self) -> Optional[str]:
        if self.vocabulary:
            return random.choice(self.vocabulary)
        return None


class TriviaEngine:
    def __init__(self, graph: CampusGraph, auto_correct: bool = False):
        self.graph = graph
        self.auto_correct = auto_correct

    def ask_mc_question(self) -> bool:
        question = self.graph.get_trivia_question()
        if question is None:
            return self.ask_vocab_question()
        print('\nSUSTAINABILITY QUESTION:')
        print(question['text'])
        if self.auto_correct:
            print('Auto-answer enabled: assuming correct.')
            return True
        user_answer = input('Answer: ').strip().upper()
        correct = user_answer == question['answer'].strip().upper()
        print('Correct!' if correct else f'Wrong. Expected {question["answer"]}.')
        return correct

    def ask_vocab_question(self) -> bool:
        term = self.graph.get_vocab_term()
        if term is None:
            print('No vocabulary available for trivia.')
            return True
        print(f"Is '{term}' a sustainability-related word? (yes/no)")
        if self.auto_correct:
            print('Auto-answer enabled: assuming correct.')
            return True
        answer = input('Answer: ').strip().lower()
        return answer in ('yes', 'y')

    def apply_trivia_bonus(self, base_cost: float) -> float:
        correct = self.ask_mc_question()
        if correct:
            print('Sustainability knowledge helped reduce cost!')
            return base_cost * 0.9
        print('Incorrect answer increases action cost.')
        return base_cost * 1.1

    def placement_bonus(self, base_value: float) -> float:
        correct = self.ask_mc_question()
        if correct:
            return base_value * 1.25
        return base_value * 0.6


class SearchGame:
    def __init__(self, graph: CampusGraph, trivia: TriviaEngine):
        self.graph = graph
        self.trivia = trivia

    def _edge_cost(self, from_node: str, to_node: str, dist: float) -> float:
        penalty = self.graph.get_node_penalty(to_node)
        return dist * 100.0 + penalty

    def plan_route(self, start: str, goal: str, use_trivia: bool = True) -> Dict[str, object]:
        start_node = self.graph.resolve_name(start) or start
        goal_node = self.graph.resolve_name(goal) or goal
        if start_node not in self.graph.all_nodes or goal_node not in self.graph.all_nodes:
            raise ValueError(f'Unknown start or goal: {start} / {goal}')

        trivia_factor = 1.0
        if use_trivia:
            trivia_factor = 0.9 if self.trivia.ask_mc_question() else 1.1

        frontier: List[Tuple[float, str]] = []
        heapq.heappush(frontier, (0.0, start_node))
        came_from: Dict[str, Optional[str]] = {start_node: None}
        cost_so_far: Dict[str, float] = {start_node: 0.0}

        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal_node:
                break
            for neighbor, dist in self.graph.neighbors(current):
                new_cost = cost_so_far[current] + self._edge_cost(current, neighbor, dist) * trivia_factor
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self.graph.heuristic(neighbor, goal_node)
                    heapq.heappush(frontier, (priority, neighbor))
                    came_from[neighbor] = current

        if goal_node not in came_from:
            return {'path': [], 'cost': float('inf')}
        path = []
        node = goal_node
        while node is not None:
            path.append(node)
            node = came_from[node]
        path.reverse()
        return {'path': path, 'cost': cost_so_far[goal_node], 'start': start_node, 'goal': goal_node}


class ResourceCSP:
    def __init__(self, graph: CampusGraph, max_resources: int = 4):
        self.graph = graph
        self.max_resources = max_resources
        self.variables = self._select_candidate_nodes()
        self.domain = ['none', 'recycling', 'compost']

    def _select_candidate_nodes(self) -> List[str]:
        categories = {'dining', 'student_center', 'residential', 'academic', 'energy_research'}
        candidates = [name for name, info in self.graph.all_nodes.items() if str(info.get('category', '')).lower() in categories]
        if len(candidates) <= 6:
            return candidates
        return sorted(candidates, key=lambda n: -self.graph.get_node_score(n))[:6]

    def _valid_assignment(self, assignment: Dict[str, str]) -> bool:
        selected = [node for node, value in assignment.items() if value != 'none']
        if len(selected) > self.max_resources:
            return False
        categories = {self.graph.all_nodes[node]['category'] for node in selected}
        required = {'dining', 'student_center', 'residential'}
        if not required.intersection(categories):
            return False
        for node, value in assignment.items():
            if value == 'compost' and self.graph.all_nodes[node]['category'] not in ('dining', 'student_center', 'residential'):
                return False
        return True

    def _partial_valid(self, assignment: Dict[str, str]) -> bool:
        selected = [value for value in assignment.values() if value != 'none']
        if len(selected) > self.max_resources:
            return False
        return True

    def solve(self) -> Dict[str, str]:
        assignment: Dict[str, str] = {}
        order = self.variables

        def backtrack(index: int) -> Optional[Dict[str, str]]:
            if index >= len(order):
                if self._valid_assignment(assignment):
                    return dict(assignment)
                return None
            node = order[index]
            for value in self.domain:
                assignment[node] = value
                if not self._partial_valid(assignment):
                    continue
                result = backtrack(index + 1)
                if result is not None:
                    return result
            assignment.pop(node, None)
            return None

        solution = backtrack(0)
        return solution or {}

    def score(self, assignment: Dict[str, str]) -> float:
        score = 0.0
        values = {'recycling': 3.0, 'compost': 4.0}
        for node, value in assignment.items():
            if value != 'none':
                score += values.get(value, 0.0) + self.graph.get_node_score(node) * 0.5
        return score


class MinimaxShowdown:
    def __init__(self, graph: CampusGraph, csp_solution: Dict[str, str], trivia: TriviaEngine):
        self.graph = graph
        self.csp_solution = csp_solution
        self.trivia = trivia
        self.buildings = list(csp_solution.keys())
        self.max_placement = 2

    def initial_state(self) -> Dict[str, object]:
        return {
            'placements': {node: 'none' for node in self.buildings},
            'penalties': {node: 0 for node in self.buildings},
            'placements_left': self.max_placement,
        }

    def _evaluate(self, state: Dict[str, object]) -> float:
        total = 0.0
        placements = state['placements']
        penalties = state['penalties']
        for node, value in placements.items():
            if value == 'recycling':
                total += 3.0 + self.graph.get_node_score(node) * 0.4
            elif value == 'compost':
                total += 4.0 + self.graph.get_node_score(node) * 0.5
        for node, count in penalties.items():
            total -= 2.5 * count
        return total

    def _max_actions(self, state: Dict[str, object]) -> List[Tuple[str, str]]:
        if state['placements_left'] <= 0:
            return []
        return [(node, action) for node, value in state['placements'].items() if value == 'none' for action in ('recycling', 'compost')]

    def _min_actions(self, state: Dict[str, object]) -> List[str]:
        return [node for node, count in state['penalties'].items() if count == 0]

    def _apply(self, state: Dict[str, object], action, player: str) -> Dict[str, object]:
        new_state = {
            'placements': dict(state['placements']),
            'penalties': dict(state['penalties']),
            'placements_left': state['placements_left'],
        }
        if player == 'max':
            node, resource = action
            new_state['placements'][node] = resource
            new_state['placements_left'] = max(0, state['placements_left'] - 1)
        else:
            target = action
            new_state['penalties'][target] += 1
        return new_state

    def minimax(self, state: Dict[str, object], depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[float, Optional[object]]:
        if depth == 0:
            return self._evaluate(state), None
        if maximizing_player:
            best_value = -math.inf
            best_action = None
            for action in self._max_actions(state):
                child = self._apply(state, action, 'max')
                value, _ = self.minimax(child, depth - 1, alpha, beta, False)
                if value > best_value:
                    best_value = value
                    best_action = action
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return best_value, best_action
        else:
            best_value = math.inf
            best_action = None
            for action in self._min_actions(state):
                child = self._apply(state, action, 'min')
                value, _ = self.minimax(child, depth - 1, alpha, beta, True)
                if value < best_value:
                    best_value = value
                    best_action = action
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return best_value, best_action

    def suggest_move(self, state: Dict[str, object], depth: int = 3) -> Optional[Tuple[str, str]]:
        _, action = self.minimax(state, depth, -math.inf, math.inf, True)
        return action

    def play_interactive(self, depth: int = 3) -> Dict[str, object]:
        state = self.initial_state()
        print('\nStarting Green Coverage Showdown\n')
        player_turn = True
        while True:
            if player_turn:
                if state['placements_left'] <= 0:
                    print('No placement actions left.')
                    break
                action = self.suggest_move(state, depth)
                if action is None:
                    break
                node, resource = action
                print(f'Placing {resource} at {node}.')
                if self.trivia.ask_mc_question():
                    print('Placement succeeds with sustainability bonus.')
                else:
                    print('Wrong answer: placement is less effective.')
                    resource = 'recycling' if resource == 'compost' else resource
                state = self._apply(state, (node, resource), 'max')
            else:
                options = self._min_actions(state)
                if not options:
                    break
                target = random.choice(options)
                print(f'Opponent triggers inefficiency at {target}.')
                state = self._apply(state, target, 'min')
            player_turn = not player_turn
        print('\nFinal state:')
        for node, resource in state['placements'].items():
            if resource != 'none':
                print(f' - {node}: {resource}')
        for node, penalty in state['penalties'].items():
            if penalty > 0:
                print(f' - {node}: penalty {penalty}')
        total = self._evaluate(state)
        print(f'Final evaluation score: {total:.2f}')
        return state


class SustainabilityGameCLI:
    def __init__(self, data_dir: str = 'data', auto: bool = False):
        self.graph = CampusGraph(data_dir)
        self.trivia = TriviaEngine(self.graph, auto_correct=auto)
        self.search = SearchGame(self.graph, self.trivia)
        self.csp = ResourceCSP(self.graph)
        self.showdown = MinimaxShowdown(self.graph, self.csp.solve(), self.trivia)

    def show_search(self, start: str, goal: str, use_trivia: bool = True) -> None:
        print(f'Planning sustainable route from "{start}" to "{goal}"...')
        result = self.search.plan_route(start, goal, use_trivia=use_trivia)
        if not result['path']:
            print('No route found.')
            return
        print('Path found:')
        for node in result['path']:
            score = self.graph.get_node_score(node)
            print(f'  - {node} (sustainability score {score:.2f})')
        print(f'Total route cost: {result["cost"]:.2f}')

    def show_csp(self) -> None:
        print('Solving resource placement CSP...')
        solution = self.csp.solve()
        if not solution:
            print('No CSP solution found.')
            return
        print('Resource placement:')
        for node, resource in solution.items():
            if resource != 'none':
                print(f'  - {node}: {resource}')
        print(f'Projected sustainability score: {self.csp.score(solution):.2f}')

    def show_showdown(self) -> None:
        print('Starting minimax sustainability showdown...')
        self.showdown.play_interactive()

    def run_monte_carlo(self, start: str, goal: str, runs: int = 100) -> None:
        costs = []
        for i in range(runs):
            result = self.search.plan_route(start, goal, use_trivia=False)
            costs.append(result['cost'])
        if not costs:
            print('No Monte Carlo results.')
            return
        print(f'Average route cost over {runs} runs: {sum(costs) / len(costs):.2f}')
        print(f'Min cost: {min(costs):.2f}, max cost: {max(costs):.2f}')
        try:
            import statistics
            print(f'STD: {statistics.pstdev(costs):.2f}')
        except Exception:
            pass
