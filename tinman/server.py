#!/usr/bin/env python3

import argparse
import sys
import os
import hashlib
import json
import subprocess

from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField

from simple_steem_client.client import SteemRemoteBackend, SteemInterface

from . import submit

INITMINER_WIF = "5JNHfZYKGaomSFvd4NUdQ9qMcEAC43kujbfjueTHpVapX1Kzq2n"

class ReusableForm(Form):
    new_account_name = TextField('New Account Name:', validators=[validators.required()])

def main(argv):
    parser = argparse.ArgumentParser(prog=argv[0], description="Web Server")
    parser.add_argument("-t", "--testserver", default="http://127.0.0.1:8190", dest="testserver", metavar="URL", help="Specify testnet steemd server")
    parser.add_argument("--signer", default="sign_transaction", dest="sign_transaction_exe", metavar="FILE", help="Specify path to sign_transaction tool")
    parser.add_argument("--get-dev-key", default="get_dev_key", dest="get_dev_key_exe", metavar="FILE", help="Specify path to get_dev_key tool")
    parser.add_argument("--secret", default="secret", dest="secret", metavar="SECERT", help="Shared secret")
    parser.add_argument("-n", "--chain-name", default="", dest="chain_name", metavar="CN", help="Specify chain name")
    parser.add_argument("-c", "--chain-id", default="", dest="chain_id", metavar="CID", help="Specify chain ID")
    parser.add_argument("--timeout", default=5.0, type=float, dest="timeout", metavar="SECONDS", help="API timeout")
    args = parser.parse_args(argv[1:])
    
    timeout = args.timeout
    
    backend = SteemRemoteBackend(nodes=[args.testserver], appbase=True, min_timeout=timeout, max_timeout=timeout)
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
                # Save the comment here.
                
                key_types = ["owner", "active", "posting", "memo"]
                keys = {}
                
                for key_type in key_types:
                    result_bytes = subprocess.check_output([args.get_dev_key_exe, args.secret, key_type + "-" + new_account_name])
                    result_str = result_bytes.decode("utf-8")
                    result_json = json.loads(result_str.strip())
                    
                    keys[key_type] = result_json[0]
                
                tx = {
                    "operations":[
                        {"type":"account_create_operation","value":{
                            "creator":"initminer",
                            "new_account_name":new_account_name,
                            "fee":{"amount":"0","nai":"@@000000021","precision":3},
                            "owner":{"account_auths":["tnman",1],"key_auths":[[keys["owner"]["public_key"],1]],"weight_threshold":1},
                            "active":{"account_auths":["tnman",1],"key_auths":[[keys["active"]["public_key"],1]],"weight_threshold":1},
                            "posting":{"account_auths":["tnman",1],"key_auths":[[keys["posting"]["public_key"],1]],"weight_threshold":1},
                            "memo_key":keys["memo"]["public_key"],
                            "json_metadata":""}
                        }, {"type":"transfer_to_vesting_operation","value":{
                            "amount":{"amount":"1000000","nai":"@@000000021","precision":3},
                            "from":"initminer",
                            "to":new_account_name}
                        }
                    ],
                    "signatures":[]}
                
                result = signer.sign_transaction(tx, INITMINER_WIF)
                if "error" in result:
                    print("could not sign transaction", tx, "due to error:", result["error"])
                else:
                    tx["signatures"].append(result["result"]["sig"])
                steemd.network_broadcast_api.broadcast_transaction(trx=tx)
                    
                flash("Account Created: " + new_account_name)
                
                for key in keys:
                    flash(key + ": " + keys[key]["private_key"])
            else:
                flash('All the form fields are required.')
     
        return render_template('account_create.html', form=form)
    
    app.run()

if __name__ == "__main__":
    main(sys.argv)
