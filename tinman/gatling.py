#!/usr/bin/env python3

import argparse
import datetime
import json
import sys

from . import prockey
from . import util

STEEM_GENESIS_TIMESTAMP = 1451606400
STEEM_BLOCK_INTERVAL = 3

def stream_actions(conf):
    keydb = prockey.ProceduralKeyDatabase()

    start_time = datetime.datetime.strptime(conf["start_time"], "%Y-%m-%dT%H:%M:%S")
    genesis_time = datetime.datetime.utcfromtimestamp(STEEM_GENESIS_TIMESTAMP)
    miss_blocks = int((start_time - genesis_time).total_seconds()) // STEEM_BLOCK_INTERVAL
    miss_blocks = max(miss_blocks-1, 0)

    # stream here

    return

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Generate transactions for Steem testnet")
    parser.add_argument("-c", "--conffile", default="", dest="conffile", metavar="FILE", help="Specify configuration file")
    parser.add_argument("-o", "--outfile", default="-", dest="outfile", metavar="FILE", help="Specify output file, - means stdout")
    args = parser.parse_args(argv[1:])

    with open(args.conffile, "r") as f:
        conf = json.load(f)

    if args.outfile == "-":
        outfile = sys.stdout
    else:
        outfile = open(args.outfile, "w")

    for action in stream_actions(conf):
        outfile.write(util.action_to_str(action))
        outfile.write("\n")

    outfile.flush()
    if args.outfile != "-":
        outfile.close()

if __name__ == "__main__":
    main(sys.argv)
