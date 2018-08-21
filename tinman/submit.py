#!/usr/bin/env python3

from simple_steem_client.client import SteemRemoteBackend, SteemInterface

from binascii import hexlify, unhexlify

import argparse
import datetime
import hashlib
import itertools
import json
import struct
import subprocess
import sys
import time
import traceback

from . import util

STEEM_GENESIS_TIMESTAMP = 1451606400
STEEM_BLOCK_INTERVAL = 3

class TransactionSigner(object):
    def __init__(self, sign_transaction_exe=None, chain_id=None):
        if(chain_id is None):
            self.proc = subprocess.Popen([sign_transaction_exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        else:
            self.proc = subprocess.Popen([sign_transaction_exe, "--chain-id="+chain_id], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return

    def sign_transaction(self, tx, wif):
        json_data = json.dumps({"tx":tx, "wif":wif}, separators=(",", ":"), sort_keys=True)
        json_data_bytes = json_data.encode("ascii")
        self.proc.stdin.write(json_data_bytes)
        self.proc.stdin.write(b"\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline().decode("utf-8")
        return json.loads(line)

class CachedDgpo(object):
    def __init__(self, timefunc=time.time, refresh_interval=1.0, steemd=None):
        self.timefunc = timefunc
        self.refresh_interval = refresh_interval
        self.steemd = steemd

        self.dgpo = None
        self.last_refresh = self.timefunc()

        return

    def reset(self):
        self.dgpo = None

    def get(self):
        now = self.timefunc()
        if (now - self.last_refresh) > self.refresh_interval:
            self.reset()
        if self.dgpo is None:
            self.dgpo = self.steemd.database_api.get_dynamic_global_properties(a=None)
            self.last_refresh = now
        return self.dgpo

def wait_for_real_time(when):
    while True:
        rtc_now = datetime.datetime.utcnow()
        if rtc_now >= when:
            break
        time.sleep(0.4)

def generate_blocks(steemd, args, cached_dgpo=None, now=None, produce_realtime=False):
    if args["count"] <= 0:
        return

    miss_blocks = args.get("miss_blocks", 0)

    if not produce_realtime:
        steemd.debug_node_api.debug_generate_blocks(
            debug_key="5JNHfZYKGaomSFvd4NUdQ9qMcEAC43kujbfjueTHpVapX1Kzq2n",
            count=args["count"],
            skip=0,
            miss_blocks=miss_blocks,
            edit_if_needed=False,
            )
        return
    dgpo = cached_dgpo.get()
    now = dgpo["time"]

    head_block_time = datetime.datetime.strptime(dgpo["time"], "%Y-%m-%dT%H:%M:%S")
    next_time = head_block_time + datetime.timedelta(seconds=3*(1+miss_blocks))

    print("wait_for_real_time( {} )".format(next_time))
    wait_for_real_time(next_time)
    print("calling debug_generate_blocks, miss_blocks={}".format(miss_blocks))
    steemd.debug_node_api.debug_generate_blocks(
           debug_key="5JNHfZYKGaomSFvd4NUdQ9qMcEAC43kujbfjueTHpVapX1Kzq2n",
           count=1,
           skip=0,
           miss_blocks=miss_blocks,
           edit_if_needed=False,
           )
    print("entering loop")
    for i in range(1, args["count"]):
        next_time += datetime.timedelta(seconds=3)
        wait_for_real_time(next_time)
        steemd.debug_node_api.debug_generate_blocks(
               debug_key="5JNHfZYKGaomSFvd4NUdQ9qMcEAC43kujbfjueTHpVapX1Kzq2n",
               count=1,
               skip=0,
               miss_blocks=0,
               edit_if_needed=False,
               )
    return

def main(argv):

    parser = argparse.ArgumentParser(prog=argv[0], description="Submit transactions to Steem")
    parser.add_argument("-t", "--testserver", default="http://127.0.0.1:8190", dest="testserver", metavar="URL", help="Specify testnet steemd server with debug enabled")
    parser.add_argument("-txb", "--transactions_per_block", default="-1", dest="transactions_per_block", metavar="Number", type=int, help="The number of transactions to send before triggering block production with the 'wait_block' operation")
    parser.add_argument("--signer", default="sign_transaction", dest="sign_transaction_exe", metavar="FILE", help="Specify path to sign_transaction tool")
    parser.add_argument("-i", "--input-file", default="-", dest="input_file", metavar="FILE", help="File to read transactions from")
    parser.add_argument("-f", "--fail-file", default="-", dest="fail_file", metavar="FILE", help="File to write failures, - for stdout, die to quit on failure")
    parser.add_argument("-c", "--chain-id", default="", dest="chain_id", metavar="CID", help="Specify chain ID")
    parser.add_argument("--timeout", default=5.0, type=float, dest="timeout", metavar="SECONDS", help="API timeout")
    parser.add_argument("--realtime", dest="realtime", action="store_true", help="Wait when asked to produce blocks in the future")
    args = parser.parse_args(argv[1:])

    die_on_fail = False
    if args.fail_file == "-":
        fail_file = sys.stdout
    elif args.fail_file == "die":
        fail_file = sys.stdout
        die_on_fail = True
    else:
        fail_file = open(args.fail_file, "w")

    if args.input_file == "-":
        input_file = sys.stdin
    else:
        input_file = open(args.input_file, "r")

    timeout = args.timeout

    backend = SteemRemoteBackend(nodes=[args.testserver], appbase=True, min_timeout=timeout, max_timeout=timeout)
    steemd = SteemInterface(backend)
    sign_transaction_exe = args.sign_transaction_exe
    produce_realtime = args.realtime

    cached_dgpo = CachedDgpo(steemd=steemd)

    if args.chain_id != "":
        chain_id = hashlib.sha256(args.chain_id).digest()
    else:
        chain_id = None

    signer = TransactionSigner(sign_transaction_exe=sign_transaction_exe, chain_id=chain_id)
    transaction_count = -1
    for line in input_file:
        line = line.strip()
        cmd, args = json.loads(line)

        try:
            if cmd == "wait_blocks" :
                if args.transactions_per_block == -1 :
                    generate_blocks(steemd, args, cached_dgpo=cached_dgpo, produce_realtime=produce_realtime)
                    cached_dgpo.reset()
            elif cmd == "submit_transaction":
                transaction_count += 1;
                tx = args["tx"]
                dgpo = cached_dgpo.get()
                tx["ref_block_num"] = dgpo["head_block_number"] & 0xFFFF
                tx["ref_block_prefix"] = struct.unpack_from("<I", unhexlify(dgpo["head_block_id"]), 4)[0]
                head_block_time = datetime.datetime.strptime(dgpo["time"], "%Y-%m-%dT%H:%M:%S")
                expiration = head_block_time+datetime.timedelta(minutes=1)
                expiration_str = expiration.strftime("%Y-%m-%dT%H:%M:%S")
                tx["expiration"] = expiration_str

                wif_sigs = tx["wif_sigs"]
                del tx["wif_sigs"]

                sigs = []
                for wif in wif_sigs:
                    if not isinstance(wif_sigs, list):
                        raise RuntimeError("wif_sigs is not list")
                    result = signer.sign_transaction(tx, wif)
                    if "error" in result:
                        print("could not sign transaction", tx, "due to error:", result["error"])
                    else:
                        sigs.append(result["result"]["sig"])
                tx["signatures"] = sigs
                print("bcast:", json.dumps(tx, separators=(",", ":")))
                steemd.network_broadcast_api.broadcast_transaction(trx=tx)
            elif cmd == "transaction_count" and transaction_count == -1 and args.transactions_per_block > 0:
                #If our args include 'transactions_per_block' we're expecting a snapshot that includes the number of transactions
                #That means we can calculate the start time 'on the fly' and get *very* close to a real-time transition to normal block production
                transaction_count = 0
                genesis_time = datetime.datetime.utcfromtimestamp(STEEM_GENESIS_TIMESTAMP)
                bootstrap_completion_target_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes = 15))
                transaction_start_seconds = int(bootstrap_completion_target_time.total_seconds()) - ((args.count // args.transactions_per_block) * STEEM_BLOCK_INTERVAL)
                miss_blocks = {'count' : (transaction_start_seconds - genesis_time) // STEEM_BLOCK_INTERVAL }
                miss_blocks = max(miss_blocks-1, 0)
                generate_blocks(steemd, miss_blocks, cached_dgpo=cached_dgpo, produce_realtime=produce_realtime)

            if  args.transactions_per_block > 0 and (0 == transaction_count % args.transactions_per_block) :
                generate_blocks(steemd, args, cached_dgpo=cached_dgpo, produce_realtime=produce_realtime)
                cached_dgpo.reset()
        except Exception as e:
            fail_file.write(json.dumps([cmd, args, str(e)])+"\n")
            fail_file.flush()
            if die_on_fail:
                raise
    if  args.transactions_per_block > 0 :
        print("Because transactions_per_block was specificed we should be close to the present moment.")
        print("skipping any last-instruction empty block production")

if __name__ == "__main__":
    main(sys.argv)
