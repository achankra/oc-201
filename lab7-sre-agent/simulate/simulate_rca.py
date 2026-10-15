#!/usr/bin/env python3
"""Local stand-in for the SRE agent's log analysis.

It does not call a model and it is not the SRE agent. It applies fixed rules to a
log file: count the lines your alert rule matches, group them by message shape,
and report the most frequent shape and when it started.

usage: python3 simulate_rca.py LOGFILE [--match REGEX] [--threshold N]
"""
import argparse
import re
import sys
from collections import Counter, OrderedDict

TS = re.compile(r"^\[?(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\]?\s*")
SHAPES = [
    (re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"), "<id>"),
    (re.compile(r"0x[0-9a-fA-F]+"), "<hex>"),
    (re.compile(r"\d+(?:\.\d+)?"), "<n>"),
]


def shape(line):
    for rx, repl in SHAPES:
        line = rx.sub(repl, line)
    return line.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("logfile")
    ap.add_argument("--match", default="ERROR", help="regex your alert rule matches (default: ERROR)")
    ap.add_argument("--threshold", type=int, default=5, help="count at which the rule fires (default: 5)")
    a = ap.parse_args()

    try:
        rx = re.compile(a.match)
        with open(a.logfile, encoding="utf-8", errors="replace") as fh:
            lines = [ln.rstrip("\n") for ln in fh if ln.strip()]
    except (OSError, re.error) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    hits = []
    for ln in lines:
        if rx.search(ln):
            m = TS.match(ln)
            hits.append((m.group(1) if m else None, TS.sub("", ln)))

    print("SIMULATED ANALYSIS: fixed local rules, not the SRE agent, no model involved")
    print(f"log lines read:       {len(lines)}")
    print(f"lines matching '{a.match}': {len(hits)}")
    print(f"alert threshold:      {a.threshold} ({'would fire' if len(hits) >= a.threshold else 'would not fire'})")
    if not hits:
        print("\nNothing matched. Check the query against your service's logs.")
        return 0

    groups = OrderedDict()
    for ts, msg in hits:
        g = groups.setdefault(shape(msg), {"n": 0, "first": ts, "last": ts, "example": msg})
        g["n"] += 1
        g["last"] = ts or g["last"]
    ranked = sorted(groups.items(), key=lambda kv: -kv[1]["n"])

    print("\nMessage shapes, most frequent first:")
    for sh, g in ranked[:5]:
        span = f" ({g['first']} to {g['last']})" if g["first"] else ""
        print(f"  {g['n']:>4}  {sh}{span}")

    top_shape, top = ranked[0]
    print("\nLead:")
    print(f"  {top['n']} of {len(hits)} matching lines share one shape: {top_shape}")
    if top["first"]:
        print(f"  first seen {top['first']}")
    print(f"  example: {top['example']}")
    print("\nThis is where to look first. Confirm it against the logs, the wirelogs or a shell in the pod.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
