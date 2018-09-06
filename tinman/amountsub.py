#!/usr/bin/env python3

from . import util

import argparse
import json
import sys
import math

def transform_amounts(object, ratio, floor_satoshi=1):
    def intersection(a, b):
        c = [value for value in a if value in b]
        return c
    
    if isinstance(object, list):
        for e in object:
            transform_amounts(e, ratio, floor_satoshi)
    elif isinstance(object, dict):
        for key in object.keys():
            field = object[key]
            
            if not isinstance(field, dict):
                transform_amounts(field, ratio, floor_satoshi)
            elif len(intersection(["amount", "precision", "nai"], field.keys())) != 3:
                transform_amounts(field, ratio, floor_satoshi)
                continue
            else:
                if field["amount"] == "0":
                    continue
                
                new_amount = math.floor(int(field["amount"]) * ratio)
                
                if new_amount < floor_satoshi:
                    new_amount = floor_satoshi
                
                field["amount"] = str(new_amount)

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Adjust amount fields by ratio")
    parser.add_argument("-i", "--input-file", default="-", dest="input_file", metavar="FILE", help="File to read actions from")
    parser.add_argument("-o", "--output-file", default="-", dest="output_file", metavar="FILE", help="File to write actions to")
    parser.add_argument("-r", "--ratio", default="1.0", dest="ratio", metavar="FLOAT", help="Adjust amounts in op to ratio")
    parser.add_argument("-f", "--floor-satoshi", default="1", dest="floor_satoshi", metavar="INT", help="Minimum amount after ratio is applied")
    args = parser.parse_args(argv[1:])
    
    if args.output_file == "-":
        output_file = sys.stdout
    else:
        output_file = open(args.output_file, "w")

    if args.input_file == "-":
        input_file = sys.stdin
    else:
        input_file = open(args.input_file, "r")

    ratio = float(args.ratio)
    
    if ratio == 1.0:
        print("Useless ratio: 1.0")
        exit(1)
    
    for line in input_file:
        line = line.strip()
        act, act_args = json.loads(line)
        if act != "submit_transaction":
            continue
        
        if not act_args["tx"]:
            continue
        
        for op in act_args["tx"]["operations"]:
            transform_amounts(op["value"], ratio, int(args.floor_satoshi))
        
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
