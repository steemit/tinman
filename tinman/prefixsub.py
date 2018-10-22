#!/usr/bin/env python3

from . import util

import argparse
import json
import sys
import math

MAINNET_PREFIX = "STM"
TESTNET_PREFIX = "TST"
PUB_KEY_LEN = 53
MAINNET_DISABLED_WITNESS_KEY = "STM1111111111111111111111111111111114T1Anm"
TESTNET_DISABLED_WITNESS_KEY = "TST1111111111111111111111111111111114T1Anm"


def transform_prefix(object):
    if isinstance(object, list):
        for i, e in enumerate(object):
            if isinstance(e, str):
                object[i] = transform_prefix(e)
            else:
                transform_prefix(e)
    elif isinstance(object, dict):
        for key in object.keys():
            field = object[key]
            
            if isinstance(field, str):
                object[key] = transform_prefix(field)
            else:
                transform_prefix(field)
                
    elif isinstance(object, str):
        if len(object) == PUB_KEY_LEN and object[:3] == MAINNET_PREFIX:
            return TESTNET_PREFIX + object[3:]
        elif object == MAINNET_DISABLED_WITNESS_KEY:
            return TESTNET_DISABLED_WITNESS_KEY
        else:
            return object


def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Substitute prefix")
    parser.add_argument("-i", "--input-file", default="-", dest="input_file", metavar="FILE",
                        help="File to read actions from")
    parser.add_argument("-o", "--output-file", default="-", dest="output_file", metavar="FILE",
                        help="File to write actions to")
    args = parser.parse_args(argv[1:])
    
    if args.output_file == "-":
        output_file = sys.stdout
    else:
        output_file = open(args.output_file, "w")

    if args.input_file == "-":
        input_file = sys.stdin
    else:
        input_file = open(args.input_file, "r")

    for line in input_file:
        line = line.strip()
        act, act_args = json.loads(line)
        if act != "submit_transaction":
            continue
        
        if not act_args["tx"]:
            continue
        
        for op in act_args["tx"]["operations"]:
            transform_prefix(op["value"])
        
        transformed_line = json.dumps([act, act_args])
        
        output_file.write(transformed_line)
        output_file.write("\n")
        output_file.flush()
    if args.input_file != "-":
        input_file.close()
    if args.output_file != "-":
        output_file.close()


if __name__ == "__main__":
    main(sys.argv)
