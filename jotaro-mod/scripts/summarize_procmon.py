#!/usr/bin/env python3
"""Summarize a Process Monitor CSV export: did NSUNS4.exe even look for our loose files?

usage: summarize_procmon.py <procmon.csv> [--filter data_win32] [--process NSUNS4.exe]

For every path containing the filter it prints: attempts, result counts, and whether
any open (CreateFile) SUCCEEDED. This separates cause C1 (never looked / looked
elsewhere) from C2/C3 (opened it, then ignored or rejected the content).
"""
import argparse
import csv
import sys
from collections import Counter, defaultdict


def summarize(rows, needle, process):
    stats = defaultdict(lambda: {"attempts": 0, "results": Counter(), "opened": False, "ops": Counter()})
    for r in rows:
        path = r.get("Path", "")
        if needle.lower() not in path.lower():
            continue
        if process and r.get("Process Name", "").lower() != process.lower():
            continue
        s = stats[path]
        s["attempts"] += 1
        s["results"][r.get("Result", "")] += 1
        s["ops"][r.get("Operation", "")] += 1
        if r.get("Operation") == "CreateFile" and r.get("Result") == "SUCCESS":
            s["opened"] = True
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--filter", default="data_win32")
    ap.add_argument("--process", default="NSUNS4.exe")
    a = ap.parse_args(argv)
    with open(a.csv, newline="", encoding="utf-8-sig", errors="replace") as fh:
        stats = summarize(csv.DictReader(fh), a.filter, a.process)
    if not stats:
        print(f"NO rows for {a.process} with a path containing '{a.filter}'.")
        print("=> If the capture covered character select/battle, the game never looked under that folder (supports C1).")
        return 0
    for path in sorted(stats):
        s = stats[path]
        res = ", ".join(f"{k}={v}" for k, v in s["results"].most_common())
        print(f"{'OPENED ' if s['opened'] else 'NOT-OPENED'} attempts={s['attempts']:<4} {path}\n    results: {res}")
    opened = sum(1 for s in stats.values() if s["opened"])
    print(f"\n{len(stats)} path(s), {opened} opened successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
