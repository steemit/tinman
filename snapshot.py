#!/usr/bin/env python3

import argparse
import json
import steem
import sys

DATABASE_API_SINGLE_QUERY_LIMIT = 1000

from steembase.exceptions import RPCError

def list_all_accounts(steemd):
    start = ""
    last = ""
    while True:
        result = steemd.database_api.list_accounts(
           start=start,
           limit=DATABASE_API_SINGLE_QUERY_LIMIT,
           order="by_name",
           )
        making_progress = False
        for a in result["accounts"]:
            if a["name"] > last:
                yield a
                last = a["name"]
                making_progress = True
            start = last
        if not making_progress:
            break

def dump_all_accounts(steemd, outfile):
    outfile.write("[\n")
    first = True
    for a in list_all_accounts(steemd):
        if not first:
            outfile.write(",\n")
        json.dump( a, outfile, separators=(",", ":"), sort_keys=True )
        first = False
    outfile.write("\n]")

def dump_dgpo(steemd, outfile):
    dgpo = steemd.database_api.get_dynamic_global_properties(x=None)
    json.dump( dgpo, outfile, separators=(",", ":"), sort_keys=True )

def main(argv):
    parser = argparse.ArgumentParser(description="Create snapshot files for Steem")
    parser.add_argument("-s", "--server", default="http://127.0.0.1:8090", dest="server", metavar="URL", help="Specify mainnet steemd server")
    parser.add_argument("-o", "--outfile", default="-", dest="outfile", metavar="FILE", help="Specify output file, - means stdout")
    args = parser.parse_args(argv[1:])

    if args.outfile == "-":
        outfile = sys.stdout
    else:
        outfile = open(args.outfile, "w")

    steemd = steem.Steem(nodes=[args.server])
    outfile.write("{\n")
    outfile.write('"dynamic_global_properties":')
    dump_dgpo(steemd, outfile)
    outfile.write(',\n"accounts":')
    dump_all_accounts(steemd, outfile)
    outfile.write("\n}\n")
    outfile.flush()
    if args.outfile != "-":
        outfile.close()
    return

if __name__ == "__main__":
    main(sys.argv)
