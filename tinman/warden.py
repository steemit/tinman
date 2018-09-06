#!/usr/bin/env python3

import argparse
import datetime

from simple_steem_client.client import SteemRemoteBackend, SteemInterface

PREFLIGHT_GO = 'go'
PREFLIGHT_NOGO = 'nogo'

def main(argv):
    """
    Checks basic node suitability for gatling phase.
    """
    parser = argparse.ArgumentParser(prog=argv[0], description="Generate transactions for Steem testnet")
    parser.add_argument("-s", "--server", default="http://127.0.0.1:8090", dest="server", metavar="URL", help="Specify steemd server to watch over")
    args = parser.parse_args(argv[1:])
    
    backend = SteemRemoteBackend(nodes=[args.server], appbase=True, max_timeout=0.0, max_retries=0)
    steemd = SteemInterface(backend)
    passfail = []
    
    config = steemd.database_api.get_config(x=None)
    dgpo = steemd.database_api.get_dynamic_global_properties(x=None)
    head_block_time = datetime.datetime.strptime(dgpo["time"], "%Y-%m-%dT%H:%M:%S")
    rtc_now = datetime.datetime.utcnow()
    diff = rtc_now - head_block_time
    diff = diff.total_seconds()
    block_interval = config["STEEM_BLOCK_INTERVAL"]
    
    if config["IS_TEST_NET"]:
        print("[√] testnet: true")
        passfail.append(PREFLIGHT_GO)
    else:
        print("[X] testnet: false")
        passfail.append(PREFLIGHT_NOGO)
    
    if diff < 0:
        print("[X] head block time: %s seconds into the future" % abs(diff))
        passfail.append(PREFLIGHT_NOGO)
    elif diff - block_interval > 0:
        print("[X] head block time: %s seconds behind" % diff)
        passfail.append(PREFLIGHT_NOGO)
    else:
        print("[√] head block time: within %s seconds" % block_interval)
        passfail.append(PREFLIGHT_GO)
    
    witness_schedule = steemd.database_api.get_witness_schedule(x=None)
    witnesses = witness_schedule["current_shuffled_witnesses"]
    initminer = config["STEEM_INIT_MINER_NAME"]
    
    if initminer not in witnesses:
        print("[√] witnesses: %s not present" % initminer)
        passfail.append(PREFLIGHT_GO)
    else:
        print("[X] witnesses: %s present" % initminer)
        passfail.append(PREFLIGHT_NOGO)
    
    scheduled_witnesses = witness_schedule["num_scheduled_witnesses"]
    
    if scheduled_witnesses == config["STEEM_MAX_WITNESSES"]:
        print("[√] scheduled witnesses: %s" % config["STEEM_MAX_WITNESSES"])
        passfail.append(PREFLIGHT_GO)
    else:
        print("[X] scheduled witnesses: %s" % scheduled_witnesses)
        passfail.append(PREFLIGHT_NOGO)
    
    majority_version = witness_schedule["majority_version"]
    
    if majority_version == '0.0.0':
        print("[X] majority version: 0.0.0")
        passfail.append(PREFLIGHT_NOGO)
    else:
        print("[√] majority version: %s" % majority_version)
        passfail.append(PREFLIGHT_GO)
    
    exit(PREFLIGHT_NOGO in passfail) # Also tell the caller everything is ok.
