import argparse

from .builder import build
from .config import init_project


def main():
    parser = argparse.ArgumentParser(
        prog="pybuildx",
        description="Build Python applications with one command",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "init",
        help="Initialize a PyBuildX project",
    )

    build_parser = subparsers.add_parser(
        "build",
        help="Build the application",
    )

    build_parser.add_argument(
        "--target",
        choices=["linux", "windows"],
        help="Target operating system",
    )

    args = parser.parse_args()

    if args.command == "init":
        init_project()

    elif args.command == "build":
        build(target=args.target)

    else:
        parser.print_help()
