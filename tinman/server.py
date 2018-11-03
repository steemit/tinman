#!/usr/bin/env python3

import argparse
import sys
import os
import hashlib
import json
import subprocess
import struct
import time
import datetime

from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
from binascii import hexlify, unhexlify

from simple_steem_client.client import SteemRemoteBackend, SteemInterface, SteemRPCException

from . import submit

class ReusableForm(Form):
    new_account_name = TextField('New Account Name:', validators=[validators.required()])

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Web Server")
    parser.add_argument("-c", "--conffile", default="server.conf", dest="conffile", metavar="FILE", help="Specify configuration file")
    parser.add_argument("--signer", default="sign_transaction", dest="sign_transaction_exe", metavar="FILE", help="Specify path to sign_transaction tool")
    parser.add_argument("--get-dev-key", default="get_dev_key", dest="get_dev_key_exe", metavar="FILE", help="Specify path to get_dev_key tool")
    parser.add_argument("-n", "--chain-name", default="", dest="chain_name", metavar="CN", help="Specify chain name")
    parser.add_argument("-cid", "--chain-id", default="", dest="chain_id", metavar="CID", help="Specify chain ID")
    parser.add_argument("--timeout", default=5.0, type=float, dest="timeout", metavar="SECONDS", help="API timeout")
    args = parser.parse_args(argv[1:])
    
    with open(args.conffile, "r") as f:
        conf = json.load(f)
    
    timeout = args.timeout
    
    node = conf["transaction_target"]["node"]
    shared_secret = conf["shared_secret"]
    account_creator = conf["account_creator"]
    result_bytes = subprocess.check_output([args.get_dev_key_exe, shared_secret, "active-" + account_creator])
    result_str = result_bytes.decode("utf-8")
    result_json = json.loads(result_str.strip())
    account_creator_wif = result_json[0]["private_key"]
    backend = SteemRemoteBackend(nodes=[node], appbase=True, min_timeout=timeout, max_timeout=timeout)
    steemd = SteemInterface(backend)
    sign_transaction_exe = args.sign_transaction_exe
    
    if args.chain_name != "":
        chain_id = hashlib.sha256(str.encode(args.chain_name.strip())).digest().hex()
    else:
        chain_id = None

    if args.chain_id != "":
        chain_id = args.chain_id.strip()
    
    signer = submit.TransactionSigner(sign_transaction_exe=sign_transaction_exe, chain_id=chain_id)

    template_dir = '/tmp/tinman-templates'
    static_dir = '/tmp/tinman-static'

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir, static_url_path='/static')
    app.debug = True
    
    # Temporary development secret key (for web forms).
    app.config['SECRET_KEY'] = '5333d026583fdd09f413d472b29ed39e'
 
    @app.route("/account_create", methods=['GET', 'POST'])
    def account_create():
        form = ReusableForm(request.form)
     
        print(form.errors)
        if request.method == 'POST':
            new_account_name = request.form['new_account_name']
     
            if form.validate():
                key_types = ["owner", "active", "posting", "memo"]
                keys = {}
                
                for key_type in key_types:
                    result_bytes = subprocess.check_output([args.get_dev_key_exe, shared_secret, key_type + "-" + new_account_name])
                    result_str = result_bytes.decode("utf-8")
                    result_json = json.loads(result_str.strip())
                    
                    keys[key_type] = result_json[0]
                
                tx = {
                    "operations":[
                        {"type":"account_create_operation","value":{
                            "creator":account_creator,
                            "new_account_name":new_account_name,
                            "fee":{"amount":"0","nai":"@@000000021","precision":3},
                            "owner":{"account_auths":[["tnman",1]],"key_auths":[[keys["owner"]["public_key"],1]],"weight_threshold":1},
                            "active":{"account_auths":[["tnman",1]],"key_auths":[[keys["active"]["public_key"],1]],"weight_threshold":1},
                            "posting":{"account_auths":[["tnman",1]],"key_auths":[[keys["posting"]["public_key"],1]],"weight_threshold":1},
                            "memo_key":keys["memo"]["public_key"],
                            "json_metadata":""
                        }}, {"type":"transfer_to_vesting_operation","value":{
                            "amount":{"amount":"1000000","nai":"@@000000021","precision":3},
                            "from":account_creator,
                            "to":new_account_name
                        }}
                    ],
                    "signatures":[]
                }
                
                cached_dgpo = submit.CachedDgpo(steemd=steemd)
                dgpo = cached_dgpo.get()
                tx["ref_block_num"] = dgpo["head_block_number"] & 0xFFFF
                tx["ref_block_prefix"] = struct.unpack_from("<I", unhexlify(dgpo["head_block_id"]), 4)[0]
                head_block_time = datetime.datetime.strptime(dgpo["time"], "%Y-%m-%dT%H:%M:%S")
                expiration = head_block_time+datetime.timedelta(minutes=1)
                expiration_str = expiration.strftime("%Y-%m-%dT%H:%M:%S")
                tx["expiration"] = expiration_str

                result = signer.sign_transaction(tx, account_creator_wif)
                if "error" in result:
                    print("could not sign transaction", tx, "due to error:", result["error"])
                else:
                    tx["signatures"].append(result["result"]["sig"])
                
                print("bcast:", json.dumps(tx, separators=(",", ":")))
                
                try:
                    steemd.network_broadcast_api.broadcast_transaction(trx=tx)
                    flash("Account Created: " + new_account_name)
                    
                    for key in keys:
                        flash(key + ": " + keys[key]["private_key"])
                except SteemRPCException as e:
                    cause = e.args[0].get("error")
                    if cause:
                        message = cause.get("message")
                        data = cause.get("data")
                    else:
                        message = str(e)
                    print(str(e))
                    flash("Unable to create account: " + message)
            else:
                flash('All the form fields are required.')
     
        return render_template('account_create.html', form=form)
    
    app.run()

if __name__ == "__main__":
    main(sys.argv)
