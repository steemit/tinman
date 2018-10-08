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
        # We do not have random access, so we must load the whole thing in
        # memory.  And we cannot output messages.
        
        infile = sys.stdin
        
        snapshot = json.load(infile, object_pairs_hook=collections.OrderedDict)
        snapshot["witnesses"] = []
        snapshot["accounts"] = heapq.nlargest(sample_size, snapshot["accounts"],
            key=lambda a : int(a["balance"]["amount"]))
    else:
        # We have random access!
        
        try:
            import ijson.backends.yajl2_cffi as ijson
            from cffi import FFI
            YAJL2_CFFI_AVAILABLE = True
        except ImportError:
            import ijson
            YAJL2_CFFI_AVAILABLE = False
        
        if not YAJL2_CFFI_AVAILABLE:
            print("Warning: could not load yajl, falling back to default backend for ijson.")
        
        infile = open(args.infile, "rb")

        account_balances = {}
        snapshot = {
          "dynamic_global_properties": {
            "total_vesting_fund_steem": {}
          },
          "accounts": [],
          "witnesses": []
        }

        fund = snapshot["dynamic_global_properties"]["total_vesting_fund_steem"]
        for prefix, event, value in ijson.parse(infile):
            if prefix == "dynamic_global_properties.total_vesting_fund_steem.amount":
                fund["amount"] = value
            elif prefix == "dynamic_global_properties.total_vesting_fund_steem.precision":
                fund["precision"] = value
            elif prefix == "dynamic_global_properties.total_vesting_fund_steem.nai":
                fund["nai"] = value
            if len(fund.keys()) > 2:
                break
        
        print("Captured:", snapshot["dynamic_global_properties"])
        
        infile.seek(0)
        for a in ijson.items(infile, "accounts.item"):
            account_balances[a["name"]] = a["balance"]["amount"]
            
            if len(account_balances) % 100000 == 0:
                print("Balances so far:", len(account_balances))
        
        top_accounts = heapq.nlargest(sample_size, account_balances,
            key=lambda a : int(account_balances[a]))
        
        print('Found top accounts:', len(top_accounts))
        
        infile.seek(0)
        for a in ijson.items(infile, "accounts.item"):
            t = len(top_accounts)
            s = len(snapshot["accounts"])
            
            if s >= t:
                break
                    
            if a["name"] in top_accounts:
                snapshot["accounts"].append(a)
                
                if s > 0 and s % 100 == 0:
                    print("Samples created:", s)
                    print("\t", '%.2f%% complete' % (s / t * 100.0))
                
        infile.close()

    if args.outfile == "-":
        outfile = sys.stdout
    else:
        print("Dumping sample ...")
        outfile = open(args.outfile, "w")
    json.dump(snapshot, outfile, separators=(",", ":"))

    if args.outfile != "-":
        outfile.close()

    return
