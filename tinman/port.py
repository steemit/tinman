#!/usr/bin/env python3

import argparse
import json
import sys

from . import prockey
from . import util
from . import simple_steem_client

def str2bool(str_arg):
    """
    Returns boolean True/False if recognized in string argument, None otherwise.
    """
    return True if str_arg.lower() == 'true' else (False if str_arg.lower() == 'false' else None)

def aquire_operations(conf, keydb):
    """
    Uses configuration file data to acquire operations from source node
    blocks/transactions and yields them one by one.
    """
    source_node = conf["transaction_source"]["node"]
    is_appbase = str2bool(conf["transaction_source"]["appbase"])
    backend = simple_steem_client.simple_steem_client.client.SteemRemoteBackend(nodes=[source_node], appbase=is_appbase)
    steemd = simple_steem_client.simple_steem_client.client.SteemInterface(backend)
    min_block = int(conf["min_block_number"])
    max_block = int(conf["max_block_number"])
    ported_operations = set(conf["ported_operations"])
    tx_signer = conf["transaction_signer"]
    for op in util.iterate_operations_from(steemd, is_appbase, min_block, max_block, ported_operations):
        yield {"operations" : [op], "wif_sigs" : [keydb.get_privkey(tx_signer)]}
    return

def repack_operations(conf):
    """
    Packs transactions acquired from source node into blocks of configured size.
    """
    keydb = prockey.ProceduralKeyDatabase()
    for b in util.batch(aquire_operations(conf, keydb), conf["transactions_per_block"]):
        yield ["wait_blocks", {"count" : 1}]
        for tx in b:
            yield ["submit_transaction", {"tx" : tx}]
    yield ["wait_blocks", {"count" : 50}]
    return

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Port transactions for Steem testnet")
    parser.add_argument("-c", "--conffile", default="", dest="conffile", metavar="FILE", help="Specify configuration file")
    parser.add_argument("-o", "--outfile", default="-", dest="outfile", metavar="FILE", help="Specify output file, - means stdout")
    args = parser.parse_args(argv[1:])

    with open(args.conffile, "r") as f:
        conf = json.load(f)

    if args.outfile == "-":
        outfile = sys.stdout
    else:
        outfile = open(args.outfile, "w")

    for action in repack_operations(conf):
        outfile.write(util.action_to_str(action))
        outfile.write("\n")

    outfile.flush()
    if args.outfile != "-":
        outfile.close()

if __name__ == "__main__":
    main(sys.argv)
