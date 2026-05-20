#!/usr/bin/env python3
import argparse

from campus_game import SustainabilityGameCLI


def main():
    parser = argparse.ArgumentParser(description='UST Sustainability Game CLI')
    parser.add_argument('--data', default='data', help='Path to the data directory')
    parser.add_argument('--mode', choices=['search', 'csp', 'showdown', 'mc'], default='search', help='Game mode')
    parser.add_argument('--start', default='Anderson Student Center', help='Start building for search mode')
    parser.add_argument('--goal', default='Frey Residence Hall', help='Goal building for search mode')
    parser.add_argument('--runs', type=int, default=100, help='Number of Monte Carlo runs')
    parser.add_argument('--auto', action='store_true', help='Enable auto trivia answer mode')
    args = parser.parse_args()

    cli = SustainabilityGameCLI(data_dir=args.data, auto=args.auto)

    if args.mode == 'search':
        cli.show_search(args.start, args.goal, use_trivia=not args.auto)
    elif args.mode == 'csp':
        cli.show_csp()
    elif args.mode == 'showdown':
        cli.show_showdown()
    elif args.mode == 'mc':
        cli.run_monte_carlo(args.start, args.runs)


if __name__ == '__main__':
    main()
