import csv
import heapq
import math
import os
import random
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def normalize_name(name: str) -> str:
    return ''.join(ch.lower() for ch in str(name) if ch.isalnum())


class DataLoader:
    def __init__(self, data_dir: str = 'data', use_subset: bool = True):
        self.data_dir = data_dir
        self.use_subset = use_subset

    def load_nodes(self) -> List[Dict[str, str]]:
        if self.use_subset:
            path = os.path.join(self.data_dir, 'ust_game_subset_15nodes.csv')
        else:
            path = os.path.join(self.data_dir, 'ust_selected_game_nodes.csv')
        with open(path, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def load_edges(self) -> List[Dict[str, str]]:
        if self.use_subset:
            path = os.path.join(self.data_dir, 'ust_game_subset_15edges.csv')
        else:
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


class TriviaGame:
    def __init__(self, data_dir: str = 'data', filename: str = 'Sustainability Trivia Game 2026.docx'):
        self.data_dir = data_dir
        self.filename = filename
        self.questions = self._load_trivia_questions()

    def _load_trivia_questions(self) -> List[Dict[str, object]]:
        path = Path(self.data_dir) / self.filename
        if not path.exists():
            return []
        with zipfile.ZipFile(path, 'r') as archive:
            xml_content = archive.read('word/document.xml')
        root = ET.fromstring(xml_content)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs = [''.join(t.text for t in p.findall('.//w:t', ns) if t.text) for p in root.findall('.//w:p', ns)]

        questions: List[Dict[str, object]] = []
        state: Optional[Dict[str, object]] = None

        def finalize_state():
            nonlocal state
            if state is None:
                return
            if state.get('answer') is not None:
                if state['type'] == 'mc' and state['options']:
                    questions.append(state)
                elif state['type'] == 'tf':
                    questions.append(state)
            state = None

        for text in paragraphs:
            if not text.strip():
                continue
            text = text.strip()
            if text.startswith('Question:'):
                finalize_state()
                state = {
                    'type': 'mc',
                    'prompt': text[len('Question:'):].strip(),
                    'options': [],
                    'answer': None,
                }
                continue
            if text.startswith('Statement:'):
                finalize_state()
                state = {
                    'type': 'tf',
                    'prompt': text[len('Statement:'):].strip(),
                    'options': ['True', 'False'],
                    'answer': None,
                }
                continue
            if text.startswith('Answer:') and state is not None:
                answer_text = text[len('Answer:'):].strip()
                if state['type'] == 'mc':
                    letter = answer_text.split('.')[0].strip().upper()
                    state['answer'] = letter
                else:
                    answer = answer_text.split('.')[0].strip().capitalize()
                    state['answer'] = 'True' if 'true' in answer.lower() else 'False'
                finalize_state()
                continue
            if state is not None:
                if state['type'] == 'mc':
                    state['options'].append(text)
                else:
                    state['prompt'] += ' ' + text
        finalize_state()
        return questions

    def _format_question(self, question: Dict[str, object]) -> str:
        text = question['prompt']
        if question['type'] == 'mc':
            letters = ['A', 'B', 'C', 'D', 'E', 'F']
            for idx, option in enumerate(question['options']):
                if idx >= len(letters):
                    break
                text += f'\n  {letters[idx]}) {option}'
        else:
            text += '\n  True\n  False'
        return text

    def ask_question(self, question: Dict[str, object]) -> bool:
        print('\nTrivia question:')
        print(self._format_question(question))
        valid_answers = set()
        if question['type'] == 'mc':
            letters = ['A', 'B', 'C', 'D', 'E', 'F']
            valid_answers = set(letters[: len(question['options'])])
            prompt = 'Your answer (A/B/C/...): '
        else:
            valid_answers = {'TRUE', 'FALSE', 'T', 'F'}
            prompt = 'Your answer (True/False): '

        while True:
            response = input(prompt).strip().upper()
            if not response:
                print('Please enter an answer.')
                continue
            if response not in valid_answers:
                print('Invalid answer. Try again.')
                continue
            if question['type'] == 'mc':
                user_answer = response[0]
                correct = user_answer == question['answer']
            else:
                user_answer = 'True' if response.startswith('T') else 'False'
                correct = user_answer == question['answer']
            if correct:
                print('Correct!')
            else:
                print(f'Incorrect. The correct answer is {question["answer"]}.')
            return correct

    def play(self, count: int = 1) -> int:
        if not self.questions:
            print('\nNo trivia questions loaded.')
            return 0
        print('\nStarting sustainability trivia challenge!')
        score = 0
        selected = random.sample(self.questions, min(count, len(self.questions)))
        for question in selected:
            if self.ask_question(question):
                score += 1
        print(f'You answered {score}/{len(selected)} correctly.')
        return score


class CampusGraph:
    def __init__(self, data_dir: str = 'data', use_subset: bool = True):
        self.loader = DataLoader(data_dir, use_subset=use_subset)
        self.nodes = self.loader.load_nodes()
        self.edges = self.loader.load_edges()
        self.distances = self.loader.load_distance_matrix()
        self.energy_assets = self.loader.load_energy_assets()
        self.sustainability_factors = self.loader.load_sustainability_factors()
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


class SearchGame:
    def __init__(self, graph: CampusGraph):
        self.graph = graph

    def _edge_cost(self, from_node: str, to_node: str, dist: float) -> float:
        penalty = self.graph.get_node_penalty(to_node)
        return dist * 100.0 + penalty

    def plan_route(self, start: str, goal: str) -> Dict[str, object]:
        start_node = self.graph.resolve_name(start) or start
        goal_node = self.graph.resolve_name(goal) or goal
        if start_node not in self.graph.all_nodes or goal_node not in self.graph.all_nodes:
            raise ValueError(f'Unknown start or goal: {start} / {goal}')

        frontier: List[Tuple[float, str]] = []
        heapq.heappush(frontier, (0.0, start_node))
        came_from: Dict[str, Optional[str]] = {start_node: None}
        cost_so_far: Dict[str, float] = {start_node: 0.0}

        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal_node:
                break
            for neighbor, dist in self.graph.neighbors(current):
                new_cost = cost_so_far[current] + self._edge_cost(current, neighbor, dist)
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
    def __init__(self, graph: CampusGraph, max_resources: int = 4, candidate_nodes: Optional[List[str]] = None):
        self.graph = graph
        self.max_resources = max_resources
        self.candidate_nodes = candidate_nodes
        self.variables = self._select_candidate_nodes()
        self.domain = ['none', 'recycling', 'compost']

    def _select_candidate_nodes(self) -> List[str]:
        if self.candidate_nodes is not None:
            candidates = [name for name in self.candidate_nodes if name in self.graph.all_nodes]
        else:
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
    def __init__(self, graph: CampusGraph, csp_solution: Dict[str, str]):
        self.graph = graph
        self.csp_solution = csp_solution
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

    def play_interactive(self, depth: int = 3, bonus_placements: int = 0) -> Dict[str, object]:
        state = self.initial_state()
        state['placements_left'] += bonus_placements
        if bonus_placements > 0:
            print(f'\nBonus placements awarded: {bonus_placements}. You have {state["placements_left"]} total placements.')
        print('\nWelcome to the Green Coverage Showdown!')
        player_turn = True
        while True:
            if player_turn:
                if state['placements_left'] <= 0:
                    print('No placement actions left.')
                    break
                print(f'\nYour turn: {state["placements_left"]} placement(s) remaining.')
                actions = self._max_actions(state)
                if not actions:
                    print('No valid placement actions available.')
                    break
                for index, (node, resource) in enumerate(actions, start=1):
                    print(f'  {index}) place {resource} at {node}')
                print('  s) use suggested best action')
                choice = input('Choose an action number or "s": ').strip().lower()
                if choice == 's':
                    suggestion = self.suggest_move(state, depth)
                    if suggestion is None:
                        print('No suggestion available. Ending showdown.')
                        break
                    node, resource = suggestion
                    print(f'Auto-selected suggestion: place {resource} at {node}.')
                    state = self._apply(state, (node, resource), 'max')
                else:
                    try:
                        index = int(choice)
                    except ValueError:
                        print('Invalid input. Please enter a number or "s".')
                        continue
                    if not 1 <= index <= len(actions):
                        print('Invalid choice. Try again.')
                        continue
                    state = self._apply(state, actions[index - 1], 'max')
            else:
                options = self._min_actions(state)
                if not options:
                    print('Opponent has no targets left.')
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
    def __init__(self, data_dir: str = 'data', use_subset: bool = True):
        self.graph = CampusGraph(data_dir, use_subset=use_subset)
        self.search = SearchGame(self.graph)
        self.csp = ResourceCSP(self.graph)
        self.showdown = MinimaxShowdown(self.graph, self.csp.solve())
        self.trivia = TriviaGame(data_dir)

    def _prompt_yes_no(self, prompt: str) -> bool:
        while True:
            choice = input(f'{prompt} (y/n): ').strip().lower()
            if choice in {'y', 'yes'}:
                return True
            if choice in {'n', 'no'}:
                return False
            print('Please enter y or n.')

    def _suggest_building_matches(self, text: str) -> List[str]:
        text = text.lower()
        return [name for name in self.graph.all_nodes if text in name.lower()][:8]

    def _prompt_building(self, prompt_text: str) -> str:
        while True:
            entry = input(prompt_text).strip()
            if not entry:
                print('Please enter a building name.')
                continue
            resolved = self.graph.resolve_name(entry) or entry
            if resolved in self.graph.all_nodes:
                return resolved
            suggestions = self._suggest_building_matches(entry)
            if suggestions:
                print('Unknown building. Did you mean:')
                for suggestion in suggestions:
                    print(f'  - {suggestion}')
            else:
                print('Unknown building. Try again.')

    def _choose_alternate_neighbor(self, current: str, blocked: str) -> Optional[str]:
        alt_neighbors = [(neighbor, dist) for neighbor, dist in self.graph.neighbors(current) if neighbor != blocked]
        if not alt_neighbors:
            return None
        return min(alt_neighbors, key=lambda pair: self.search._edge_cost(current, pair[0], pair[1]))[0]

    def _neighbor_distance(self, current: str, neighbor: str) -> float:
        return next((dist for target, dist in self.graph.neighbors(current) if target == neighbor), float('inf'))

    def play_trivia_route(self, start: str, goal: str) -> None:
        if not self.trivia.questions:
            print('\nTrivia questions are not available. Cannot run trivia-locked route traversal.')
            return
        print('\nStarting trivia-locked patrol. Answer each checkpoint correctly to stay on the efficient path.')
        current = self.graph.resolve_name(start) or start
        goal_node = self.graph.resolve_name(goal) or goal
        if current not in self.graph.all_nodes or goal_node not in self.graph.all_nodes:
            print('Unknown start or goal for trivia patrol.')
            return

        visited = [current]
        correct = 0
        incorrect = 0
        blocked_step = None

        while current != goal_node:
            route = self.search.plan_route(current, goal_node)
            if not route['path'] or len(route['path']) < 2:
                print(f'No available route from {current} to {goal_node}.')
                break
            next_node = route['path'][1]
            print(f'\nCheckpoint: move from {current} to {next_node}.')
            question = random.choice(self.trivia.questions)
            if self.trivia.ask_question(question):
                correct += 1
                print(f'Correct! Proceeding to {next_node}.')
                next_cost = self._neighbor_distance(current, next_node)
                visited.append(next_node)
                current = next_node
            else:
                incorrect += 1
                blocked_step = next_node
                alternative = self._choose_alternate_neighbor(current, blocked_step)
                if alternative is None:
                    print('No alternate path available from this checkpoint. Patrol ends here.')
                    break
                print(f'Incorrect. You are redirected to {alternative} instead of the optimal next step.')
                visited.append(alternative)
                current = alternative

        if current == goal_node:
            print(f'\nYou reached {goal_node}!')
        else:
            print(f'\nPatrol ended at {current} before reaching {goal_node}.')

        total_cost = 0.0
        for i in range(len(visited) - 1):
            step_cost = self._neighbor_distance(visited[i], visited[i + 1])
            total_cost += step_cost * 100.0 + self.graph.get_node_penalty(visited[i + 1])
        print(f'Patrol summary: visited {len(visited)} buildings, {correct} correct, {incorrect} incorrect, total effective cost {total_cost:.2f}.')

    def play(self, start: Optional[str] = None, goal: Optional[str] = None) -> None:
        print('Welcome to the UST Campus Sustainability Patrol!')
        while True:
            if not start:
                start = self._prompt_building('Enter start building: ')
            if not goal:
                goal = self._prompt_building('Enter goal building: ')
            self.show_search(start, goal)
            self.play_trivia_route(start, goal)
            if not self._prompt_yes_no('Play again with a different route?'):
                print('Thanks for playing the Campus Sustainability Patrol!')
                break
            start = None
            goal = None

    def show_search(self, start: str, goal: str) -> None:
        print(f'Planning sustainable route from "{start}" to "{goal}"...')
        result = self.search.plan_route(start, goal)
        if not result['path']:
            print('No route found.')
            return
        print('Path found:')
        for node in result['path']:
            score = self.graph.get_node_score(node)
            print(f'  - {node} (sustainability score {score:.2f})')
        print(f'Total route cost: {result["cost"]:.2f}')

        print('\nEvaluating route with CSP and minimax support along the optimal path...')
        route_nodes = result['path']
        route_csp = ResourceCSP(self.graph, candidate_nodes=route_nodes)
        placement_solution = route_csp.solve()
        if placement_solution:
            print('Suggested sustainability placements on the route:')
            for node, resource in placement_solution.items():
                if resource != 'none':
                    print(f'  - {node}: {resource}')
            print(f'Projected CSP score: {route_csp.score(placement_solution):.2f}')
        else:
            print('No CSP placement solution found along this route.')

        route_showdown = MinimaxShowdown(self.graph, placement_solution)
        state = route_showdown.initial_state()
        action = route_showdown.suggest_move(state)
        if action is not None:
            node, resource = action
            print(f'Suggested minimax action on route: place {resource} at {node} to improve robustness.')
        else:
            print('No minimax placement action suggested for this route.')
