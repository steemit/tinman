#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module allows to dump snapshot of Main Steem net contents described in the issue:
https://github.com/steemit/tinman/issues/16
"""

import argparse
import json
import sys
from simple_steem_client.client import SteemRemoteBackend, SteemInterface, SteemRPCException

from . import __version__

DATABASE_API_SINGLE_QUERY_LIMIT = 1000
MAX_RETRY = 30

# Whitelist of exceptions from transaction source (Mainnet).
TRANSACTION_SOURCE_RETRYABLE_ERRORS = [
  "Unable to acquire database lock",
  "Internal Error",
  "Server error",
  "Upstream response error"
]

def list_all_accounts(steemd):
    """ Generator function providing set of accounts existing in the Main Steem net """
    start = ""
    last = ""
    retry_count = 0
    
    while True:
        retry_count += 1
        
        try:
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
        except SteemRPCException as e:
            cause = e.args[0].get("error")
            if cause:
                message = cause.get("message")
                data = cause.get("data")
                retry = False
            
            if message and message in TRANSACTION_SOURCE_RETRYABLE_ERRORS:
                retry = True
            
            if retry and retry_count < MAX_RETRY:
                print("Recovered (tries: %s): %s" % (retry_count, message), file=sys.stderr)
                if data:
                    print(json.dumps(data, indent=2), file=sys.stderr)
            else:
                raise e

def list_all_witnesses(steemd):
    """ Generator function providing set of witnesses defined in the Main Steem net """
    start = ""
    last = ""
    w_owner = ""

    while True:
        result = steemd.database_api.list_witnesses(
            start=start,
            limit=DATABASE_API_SINGLE_QUERY_LIMIT,
            order="by_name",
            )
        making_progress = False
        for w in result["witnesses"]:
            w_owner = w["owner"]
            if w_owner > last:
                yield w_owner # Only `owner` member shall be provided
                last = w_owner
                making_progress = True
            start = last
        if not making_progress:
            break

# Helper function to reuse code related to collection dump across different usecases
def dump_collection(c, outfile):
    """ Allows to dump collection into JSON string. """
    outfile.write("[\n")
    first = True
    for o in c:
        if not first:
            outfile.write(",\n")
        json.dump( o, outfile, separators=(",", ":"), sort_keys=True )
        first = False
    outfile.write("\n]")

def dump_all_accounts(steemd, outfile):
    """ Allows to dump into the snapshot all accounts provided by Steem Net"""
    dump_collection(list_all_accounts(steemd), outfile)

def dump_all_witnesses(steemd, outfile):
    """ Allows to dump into the snapshot all witnesses provided by Steem Net"""
    dump_collection(list_all_witnesses(steemd), outfile)

def dump_dgpo(steemd, outfile):
    """ Allows to dump into the snapshot all Dynamic Global Properties Objects
        provided by Steem Net
    """
    dgpo = steemd.database_api.get_dynamic_global_properties(x=None)
    json.dump( dgpo, outfile, separators=(",", ":"), sort_keys=True )

def main(argv):
    """ Tool entry point function """
    parser = argparse.ArgumentParser(prog=argv[0], description="Create snapshot files for Steem")
    parser.add_argument("-s", "--server", default="http://127.0.0.1:8090", dest="server", metavar="URL", help="Specify mainnet steemd server")
    parser.add_argument("-o", "--outfile", default="-", dest="outfile", metavar="FILE", help="Specify output file, - means stdout")
    args = parser.parse_args(argv[1:])

    if args.outfile == "-":
        outfile = sys.stdout
    else:
        outfile = open(args.outfile, "w")

    backend = SteemRemoteBackend(nodes=[args.server], appbase=True)
    steemd = SteemInterface(backend)

    outfile.write("{\n")
    outfile.write('"metadata":{"snapshot:semver":"%s","snapshot:origin_api":"%s"}' % (__version__, args.server))
    outfile.write(',\n"dynamic_global_properties":')
    dump_dgpo(steemd, outfile)
    outfile.write(',\n"accounts":')
    dump_all_accounts(steemd, outfile)
    outfile.write(',\n"witnesses":')
    dump_all_witnesses(steemd, outfile)
    outfile.write("\n}\n")
    outfile.flush()
    if args.outfile != "-":
        outfile.close()
    return

if __name__ == "__main__":
    main(sys.argv)
