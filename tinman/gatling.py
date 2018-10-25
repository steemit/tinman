#!/usr/bin/env python3

import argparse
import json
import sys
import time
from simple_steem_client.client import SteemRemoteBackend, SteemInterface, SteemRPCException

from . import prockey
from . import util

# Whitelist of exceptions from transaction source (Mainnet).
TRANSACTION_SOURCE_RETRYABLE_ERRORS = [
  "Unable to acquire database lock",
  "Internal Error",
  "Server error",
  "Upstream response error",
  "Request Timeout"
]

MAX_RETRY = 30

def str2bool(str_arg):
    """
    Returns boolean True/False if recognized in string argument, None otherwise.
    """
    return True if str_arg.lower() == 'true' else (False if str_arg.lower() == 'false' else None)

def repack_operations(conf, keydb, min_block, max_block, from_blocks_ago, to_blocks_ago):
    """
    Uses configuration file data to acquire operations from source node
    blocks/transactions and repack them in new transactions one to one.
    """
    
    source_node = conf["transaction_source"]["node"]
    is_appbase = str2bool(conf["transaction_source"]["appbase"])
    backend = SteemRemoteBackend(nodes=[source_node], appbase=is_appbase)
    steemd = SteemInterface(backend)
    dgpo = steemd.database_api.get_dynamic_global_properties()
    
    if min_block == 0:
        min_block = dgpo["head_block_number"]

    if from_blocks_ago != -1:
        min_block = dgpo["head_block_number"] - from_blocks_ago
    
    if to_blocks_ago != -1:
        max_block = dgpo["head_block_number"] - to_blocks_ago
    
    ported_operations = conf["ported_operations"]
    ported_types = set([op["type"] for op in ported_operations])
    """ Positive value of max_block means get from [min_block_number,max_block_number) range and stop """
    if max_block > 0: 
        for op in util.iterate_operations_from(steemd, is_appbase, min_block, max_block, ported_types):
            yield op_for_role(op, conf, keydb, ported_operations)
        return
    """
    Otherwise get blocks from min_block_number to current head and again
    until you have to wait for another block to be produced (chase-then-listen mode)
    """
    old_head_block = min_block
    while True:
        dgpo = steemd.database_api.get_dynamic_global_properties()
        new_head_block = dgpo["head_block_number"]
        while old_head_block == new_head_block:
            time.sleep(1) # Theoretically 3 seconds, but most probably we won't have to wait that long.
            dgpo = steemd.database_api.get_dynamic_global_properties()
            new_head_block = dgpo["head_block_number"]
        for op in util.iterate_operations_from(steemd, is_appbase, old_head_block, new_head_block, ported_types):
            yield op_for_role(op, conf, keydb, ported_operations)
        old_head_block = new_head_block
    return

def op_for_role(op, conf, keydb, ported_operations):
    """
    Here, we match the role with the op type.  For certain types, there's more
    to do than just grab the one and only appropriate role.
    """
    tx_signer = conf["transaction_signer"]
    
    for ported_op in ported_operations:
        if ported_op["type"] == op["type"]:
            roles = ported_op["roles"]
    
    if roles and len(roles) == 1:
        # It's a trivial role that know about right in config.
        return {"operations" : [op], "wif_sigs" : [keydb.get_privkey(tx_signer, roles[0])]}
    else:
        # custom_json_operation is usually posting, but sometimes there's an elevated role.
        if op["type"] in ["custom_json_operation", "custom_binary_operation", "custom_operation"]:
            if len(op["value"]["required_posting_auths"]) > 0:
                # The role is "posting" because required_posting_auths has keys.
                return {"operations" : [op], "wif_sigs" : [keydb.get_privkey(tx_signer, "posting")]}
            else:
                # Assume "active" because there's nothing in required_posting_auths.
                return {"operations" : [op], "wif_sigs" : [keydb.get_privkey(tx_signer, "active")]}
        else:
            # Assume it's "active" as a fallback.
            return {"operations" : [op], "wif_sigs" : [keydb.get_privkey(tx_signer, "active")]}

def build_actions(conf, min_block, max_block, from_blocks_ago, to_blocks_ago):
    """
    Packs transactions rebuilt with operations acquired from source node into blocks of configured size.
    """
    keydb = prockey.ProceduralKeyDatabase()
    retry_count = 0
    
    while True:
        retry_count += 1
        
        try:
            for b in util.batch(repack_operations(conf, keydb, min_block, max_block, from_blocks_ago, to_blocks_ago), conf["transactions_per_block"]):
                for tx in b:
                    yield ["submit_transaction", {"tx" : tx}]
                    retry_count = 0
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
    return

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Port transactions for Steem testnet")
    parser.add_argument("-c", "--conffile", default="gatling.conf", dest="conffile", metavar="FILE", help="Specify configuration file")
    parser.add_argument("-f", "--from_block", default=-1, dest="min_block_num", metavar="INT", help="Stream from block_num")
    parser.add_argument("-t", "--to_block", default=-1, dest="max_block_num", metavar="INT", help="Stream to block_num")
    parser.add_argument("-fb", "--from_blocks_ago", default=-1, dest="from_blocks_ago", metavar="INT", help="Stream from relative block_num")
    parser.add_argument("-tb", "--to_blocks_ago", default=-1, dest="to_blocks_ago", metavar="INT", help="Stream to relative block_num")
    parser.add_argument("-o", "--outfile", default="-", dest="outfile", metavar="FILE", help="Specify output file, - means stdout")
    args = parser.parse_args(argv[1:])

    with open(args.conffile, "r") as f:
        conf = json.load(f)

    if args.outfile == "-":
        outfile = sys.stdout
    else:
        outfile = open(args.outfile, "w")
    
    min_block_num = int(args.min_block_num)
    max_block_num = int(args.max_block_num)
    from_blocks_ago = int(args.from_blocks_ago)
    to_blocks_ago = int(args.to_blocks_ago)
    
    if min_block_num == -1:
        min_block_num = int(conf["min_block_number"])
    
    if max_block_num == -1:
        max_block_num = int(conf["max_block_number"])
    
    for action in build_actions(conf, min_block_num, max_block_num, from_blocks_ago, to_blocks_ago):
        outfile.write(util.action_to_str(action))
        outfile.write("\n")

    outfile.flush()
    if args.outfile != "-":
        outfile.close()

if __name__ == "__main__":
    main(sys.argv)
