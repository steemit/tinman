import unittest
import shutil

from tinman import prockey
from tinman import txgen

class TestTxgen(unittest.TestCase):
    def test_create_system_accounts_bad_args(self):
        self.assertRaises(TypeError, txgen.create_system_accounts)
    
    def test_create_witnesses(self):
        keydb = prockey.ProceduralKeyDatabase()
        conf = {"accounts": {
            "init": {
                "name" : "init-{index}",
                "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"},
                "count" : 21,
                "creator" : "initminer"
            }
        }}
        
        for witness in txgen.create_system_accounts(conf, keydb, "init"):
            self.assertEqual(len(witness["operations"]), 2)
            self.assertEqual(len(witness["wif_sigs"]), 1)
            account_create_operation, transfer_to_vesting_operation = witness["operations"]
            
            self.assertEqual(account_create_operation["type"], "account_create_operation")
            value = account_create_operation["value"]
            self.assertEqual(value["fee"], {"amount" : "0", "precision" : 3, "nai" : "@@000000021"})
            self.assertEqual(value["creator"], "initminer")
            
            self.assertEqual(transfer_to_vesting_operation["type"], "transfer_to_vesting_operation")
            value = transfer_to_vesting_operation["value"]
            self.assertEqual(value["from"], "initminer")
            self.assertEqual(value["amount"], {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"})

    def test_update_witnesses(self):
        keydb = prockey.ProceduralKeyDatabase()
        conf = {"accounts": {
            "init": {
                "name" : "init-{index}",
                "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"},
                "count" : 21,
                "creator" : "initminer"
            }
        }}
        
        for witness in txgen.update_witnesses(conf, keydb, "init"):
            self.assertEqual(len(witness["operations"]), 1)
            self.assertEqual(len(witness["wif_sigs"]), 1)
            
            for op in witness["operations"]:
                self.assertEqual(op["type"], "witness_update_operation")
                value = op["value"]
                self.assertEqual(value["url"], "https://steemit.com/")
                self.assertEqual(value["props"], {})
                self.assertEqual(value["fee"], {"amount" : "0", "precision" : 3, "nai" : "@@000000021"})

    def test_vote_witnesses(self):
        keydb = prockey.ProceduralKeyDatabase()
        conf = {"accounts": {
            "init": {
                "name" : "init-{index}",
                "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"},
                "count" : 21,
                "creator" : "initminer"
            }, "elector" : {
                "name" : "elect-{index}",
                "vesting" : {"amount" : "1000000000", "precision" : 3, "nai" : "@@000000021"},
                "count" : 10,
                "round_robin_votes_per_elector" : 2,
                "random_votes_per_elector" : 3,
                "randseed" : 1234,
                "creator" : "initminer"
            }
        }}
        
        for witness in txgen.vote_accounts(conf, keydb, "elector", "init"):
            self.assertGreater(len(witness["operations"]), 1)
            self.assertEqual(len(witness["wif_sigs"]), 1)
            
            for op in witness["operations"]:
                self.assertEqual(op["type"], "account_witness_vote_operation")
                value = op["value"]
                self.assertTrue(value["approve"])

    def test_get_account_stats(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        conf = {
          "snapshot_file" : "/tmp/test-snapshot.json",
          "accounts": {}
        }
        
        account_stats = txgen.get_account_stats(conf)
        expected_account_names = {"steemit", "binance-hot", "alpha",
            "upbitsteemhot", "blocktrades", "steemit2", "ned", "holiday",
            "imadev", "muchfun", "poloniex", "gopax-deposit", "dan",
            "bithumb.sunshine", "ben", "dantheman", "openledger-dex", "bittrex",
            "huobi-withdrawal", "korbit3"
        }
        
        self.assertEqual(account_stats["account_names"], expected_account_names)
        self.assertEqual(account_stats["total_vests"], 103927115336403598)
        self.assertEqual(account_stats["total_steem"], 60859712641)

    def test_get_proportions(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        conf = {
          "snapshot_file" : "/tmp/test-snapshot.json",
          "min_vesting_per_account": {"amount" : "1", "precision" : 3, "nai" : "@@000000021"},
          "total_port_balance" : {"amount" : "200000000000", "precision" : 3, "nai" : "@@000000021"},
          "accounts": {}
        }
        account_stats = txgen.get_account_stats(conf)
        proportions = txgen.get_proportions(account_stats, conf)
        
        self.assertEqual(proportions["min_vesting_per_account"], 1)
        self.assertEqual(proportions["vest_conversion_factor"], 1469860)
        self.assertEqual(proportions["steem_conversion_factor"], 776237988251)

    def test_create_accounts(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        conf = {
          "snapshot_file" : "/tmp/test-snapshot.json",
          "min_vesting_per_account": {"amount" : "1", "precision" : 3, "nai" : "@@000000021"},
          "total_port_balance" : {"amount" : "200000000000", "precision" : 3, "nai" : "@@000000021"},
          "accounts": {"porter": {"name": "porter"}
          }
        }
        keydb = prockey.ProceduralKeyDatabase()
        account_stats = txgen.get_account_stats(conf)
        
        for account in txgen.create_accounts(account_stats, conf, keydb):
            self.assertEqual(len(account["operations"]), 3)
            self.assertEqual(len(account["wif_sigs"]), 1)
            
            for op in account["operations"]:
                value = op["value"]
                if op["type"] == "account_create_operation":
                    self.assertEqual(value["fee"], {"amount" : "0", "precision" : 3, "nai" : "@@000000021"})
                elif op["type"] == "transfer_to_vesting_operation":
                    self.assertEqual(value["from"], "porter")
                    self.assertGreater(int(value["amount"]["amount"]), 0)
                elif op["type"] == "transfer_operation":
                    self.assertEqual(value["from"], "porter")
                    self.assertGreater(int(value["amount"]["amount"]), 0)
                    self.assertEqual(value["memo"], "Ported balance")


    def test_update_accounts(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        conf = {
          "snapshot_file" : "/tmp/test-snapshot.json",
          "min_vesting_per_account": {"amount" : "1", "precision" : 3, "nai" : "@@000000021"},
          "total_port_balance" : {"amount" : "200000000000", "precision" : 3, "nai" : "@@000000021"},
          "accounts": {"manager": {"name": "tnman"}
          }
        }
        keydb = prockey.ProceduralKeyDatabase()
        account_stats = txgen.get_account_stats(conf)
        
        for account in txgen.update_accounts(account_stats, conf, keydb):
            self.assertEqual(len(account["operations"]), 1)
            self.assertEqual(len(account["wif_sigs"]), 1)
            for op in account["operations"]:
                value = op["value"]
                self.assertIn(["tnman", 1], value["owner"]["account_auths"])
            
    def test_build_actions(self):
        shutil.copyfile("test-snapshot.json", "/tmp/test-snapshot.json")
        conf = {
            "transactions_per_block" : 40,
            "snapshot_file" : "/tmp/test-snapshot.json",
            "min_vesting_per_account" : {"amount" : "1", "precision" : 3, "nai" : "@@000000021"},
            "total_port_balance" : {"amount" : "200000000000", "precision" : 3, "nai" : "@@000000021"},
            "accounts" : {
                "initminer" : {
                    "name" : "initminer",
                    "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"}
                }, "init" : {
                    "name" : "init-{index}",
                    "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"},
                    "count" : 21,
                    "creator" : "initminer"
                }, "elector" : {
                    "name" : "elect-{index}",
                    "vesting" : {"amount" : "1000000000", "precision" : 3, "nai" : "@@000000021"},
                    "count" : 10,
                    "round_robin_votes_per_elector" : 2,
                    "random_votes_per_elector" : 3,
                    "randseed" : 1234,
                    "creator" : "initminer"
                }, "porter" : {
                    "name" : "porter",
                    "creator" : "initminer",
                    "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"}
                }, "manager" : {
                    "name" : "tnman",
                    "creator" : "initminer",
                    "vesting" : {"amount" : "1000000", "precision" : 3, "nai" : "@@000000021"}
                },
                    "STEEM_MINER_ACCOUNT" : {"name" : "mners"},
                    "STEEM_NULL_ACCOUNT" : {"name" : "null"},
                    "STEEM_TEMP_ACCOUNT" : {"name" : "temp"}
                }
            }
        
        for action in txgen.build_actions(conf):
            cmd, args = action
            
            if cmd == "metadata":
                self.assertEqual(args["txgen:semver"], "0.2")
                self.assertEqual(args["txgen:transactions_per_block"], 40)
                self.assertIsNotNone(args["epoch:created"])
                self.assertEqual(args["actions:count"], 60)
                self.assertGreater(args["recommend:miss_blocks"], 28968013)
                self.assertEqual(args["snapshot:semver"], "0.2")
                self.assertEqual(args["snapshot:origin_api"], "http://calculon.local")
            elif cmd == "wait_blocks":
                self.assertGreater(args["count"], 0)
            elif cmd == "submit_transaction":
                self.assertGreater(len(args["tx"]["operations"]), 0)
            else:
                self.fail("Unexpected action: %s" % cmd)
