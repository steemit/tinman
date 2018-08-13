#!/usr/bin/env python3

import argparse
import datetime
import json
import sys
import time
from simple_steem_client.client import SteemRemoteBackend, SteemInterface

from . import prockey
from . import util

STEEM_GENESIS_TIMESTAMP = 1451606400
STEEM_BLOCK_INTERVAL = 3

def stream_actions(steemd, from_block_num, to_block_num):
    keydb = prockey.ProceduralKeyDatabase()
    genesis_time = datetime.datetime.utcfromtimestamp(STEEM_GENESIS_TIMESTAMP)
    
    if from_block_num == -1:
      dgpo = steemd.database_api.get_dynamic_global_properties()
      from_block_num =  dgpo["last_irreversible_block_num"]
    
    stream = to_block_num == -1
    
    while True:
        if stream:
            dgpo = steemd.database_api.get_dynamic_global_properties()
            to_block_num = dgpo["last_irreversible_block_num"]
        
        if from_block_num >= to_block_num:
          time.sleep(3)
          continue
        
        for block_num in range(from_block_num, to_block_num):
          block = steemd.block_api.get_block(block_num=block_num)
          for tx in block['block']['transactions']:
              tx['ref_block_num'] = None
              tx['ref_block_prefix'] = None
              tx['expiration'] = None
              tx['signatures'] = []
              yield ["submit_transaction", {"tx" : tx}]
        
        if stream:
          from_block_num = to_block_num + 1
          continue
        
        break

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Stream actions for Steem testnet")
    parser.add_argument("-s", "--server", default="http://127.0.0.1:8090", dest="server", metavar="URL", help="Specify mainnet steemd server")
    parser.add_argument("-f", "--from_block", default=-1, dest="from_block_num", metavar="integer", help="Stream from block_num")
    parser.add_argument("-t", "--to_block", default=-1, dest="to_block_num", metavar="integer", help="Stream to block_num")
    parser.add_argument("-o", "--outfile", default="-", dest="outfile", metavar="FILE", help="Specify output file, - means stdout")
    args = parser.parse_args(argv[1:])

    if args.outfile == "-":
        outfile = sys.stdout
    else:
        outfile = open(args.outfile, "w")

    backend = SteemRemoteBackend(nodes=[args.server], appbase=True)
    steemd = SteemInterface(backend)

    for action in stream_actions(steemd, int(args.from_block_num), int(args.to_block_num)):
        outfile.write(util.action_to_str(action))
        outfile.write("\n")

    outfile.flush()
    if args.outfile != "-":
        outfile.close()

if __name__ == "__main__":
    main(sys.argv)
