import csv

def load_graph():
    graph = {}
    with open('data/ust_building_edges.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(row)  # just look at what one row contains
    return graph

load_graph()
