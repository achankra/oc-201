#!/usr/bin/env python3
"""Compare declared dependencies with observed connections.

Each file lists one connection per line, written as `source -> destination`.
Blank lines and lines that start with # are ignored.

usage: python3 scripts/compare_deps.py <declared-file> <observed-file> [--strict]

--strict exits with status 1 when any observed connection was not declared.
"""
import argparse
import sys


def load(path):
    edges = set()
    with open(path) as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "->" not in line:
                sys.exit(f"{path}:{n}: expected 'source -> destination', got: {line}")
            src, dst = (part.strip() for part in line.split("->", 1))
            if not src or not dst:
                sys.exit(f"{path}:{n}: both a source and a destination are required")
            edges.add((src, dst))
    return edges


def show(title, edges, note):
    print(f"{title} ({len(edges)})")
    for src, dst in sorted(edges):
        print(f"  {src} -> {dst}")
    if edges and note:
        print(f"  {note}")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("declared", help="file with the static dependencies")
    ap.add_argument("observed", help="file with the runtime connections")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any observed connection was not declared")
    args = ap.parse_args()

    declared = load(args.declared)
    observed = load(args.observed)

    show("Declared and observed", declared & observed, "")
    undeclared = observed - declared
    show("Observed but not declared",
         undeclared,
         "Traffic works that nobody declared. Declare it, or tighten the network policy so it stops.")
    show("Declared but not observed",
         declared - observed,
         "Nothing used it while you watched. Remove it, or generate the traffic and look again.")

    if args.strict and undeclared:
        sys.exit(1)


if __name__ == "__main__":
    main()
