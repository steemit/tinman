#!/usr/bin/env python3

import argparse
import collections
import heapq
import json
import sys

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Generate transactions for Steem testnet")
    parser.add_argument("-i", "--infile", default="", dest="infile", metavar="FILE", help="Specify input snapshot, - means stdin")
    parser.add_argument("-o", "--outfile", default="-", dest="outfile", metavar="FILE", help="Specify output snapshot, - means stdout")
    args = parser.parse_args(argv[1:])

    sample_size = 2000

    if args.infile == "-":
        infile = sys.stdin
    else:
        infile = open(args.infile, "r")

    with open(args.infile, "r") as f:
        snapshot = json.load(f, object_pairs_hook=collections.OrderedDict)
        snapshot["witnesses"] = []
        snapshot["accounts"] = heapq.nlargest(sample_size, snapshot["accounts"],
            key=lambda a : int(a["balance"][0]))

    if args.infile != "-":
        infile.close()

    if args.outfile == "-":
        outfile = sys.stdout
    else:
        outfile = open(args.outfile, "w")
    json.dump(snapshot, f, separators=(",", ":"))

    if args.outfile != "-":
        outfile.close()

    return
