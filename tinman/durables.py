#!/usr/bin/env python3

import argparse
import json
import sys

from . import prockey
from . import util

def build_account_tx(account, keydb, silent=True):
    name = account["name"]
    
    return {"operations" : [{"type" : "account_create_operation", "value" : {
        "fee" : {"amount" : "0", "precision" : 3, "nai" : "@@000000021"},
        "creator" : account["creator"],
        "new_account_name" : name,
        "owner" : keydb.get_authority(name, "owner"),
        "active" : keydb.get_authority(name, "active"),
        "posting" : keydb.get_authority(name, "posting"),
        "memo_key" : keydb.get_pubkey(name, "memo"),
        "json_metadata" : "",
       }}, {"type" : "transfer_to_vesting_operation", "value" : {
        "from" : "initminer",
        "to" : name,
        "amount" : account["vesting"],
       }}],
       "wif_sigs" : [keydb.get_privkey(account["creator"])]}
    
def build_feed_tx(feed, keydb, silent=True):
    return {"operations" : [{"type" : "feed_publish_operation", "value" : {
        "publisher" : feed["publisher"],
        "exchange_rate" : feed["exchange_rate"]
       }}],
       "wif_sigs" : [keydb.get_privkey(feed["publisher"])]}
    
def build_actions(conf, silent=True):
    keydb = prockey.ProceduralKeyDatabase()
    accounts = conf["accounts"]
    feeds = conf["feeds"]
    
    for account in accounts:
      yield ["submit_transaction", {"tx" : build_account_tx(account, keydb, silent)}]
    
    for feed in feeds:
      yield ["submit_transaction", {"tx" : build_feed_tx(feed, keydb, silent)}]
    
    return

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Generate durable objects for Steem testnet")
    parser.add_argument("-c", "--conffile", default="durables.conf", dest="conffile", metavar="FILE", help="Specify configuration file")
    parser.add_argument("-o", "--outfile", default="-", dest="outfile", metavar="FILE", help="Specify output file, - means stdout")
    args = parser.parse_args(argv[1:])

    with open(args.conffile, "r") as f:
        conf = json.load(f)

    if args.outfile == "-":
        outfile = sys.stdout
    else:
        outfile = open(args.outfile, "w")

    for action in build_actions(conf, args.outfile == "-"):
        outfile.write(util.action_to_str(action))
        outfile.write("\n")

    outfile.flush()
    if args.outfile != "-":
        outfile.close()

if __name__ == "__main__":
    main(sys.argv)
