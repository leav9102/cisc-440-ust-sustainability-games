#!/usr/bin/env python3
import argparse

from campus_game import SustainabilityGameCLI


def main():
    parser = argparse.ArgumentParser(description='UST Campus Sustainability Patrol CLI')
    parser.add_argument('--data', default='data', help='Path to the data directory')
    parser.add_argument('--start', help='Start building for patrol')
    parser.add_argument('--goal', help='Goal building for patrol')
    parser.add_argument('--interactive', action='store_true', help='Run the trivia-locked interactive patrol')
    args = parser.parse_args()

    cli = SustainabilityGameCLI(data_dir=args.data)
    if args.interactive or not args.start or not args.goal:
        cli.play(start=args.start, goal=args.goal)
    else:
        cli.show_search(args.start, args.goal)


if __name__ == '__main__':
    main()
