import unittest

from tinman import util

from simple_steem_client.client import SteemRemoteBackend, SteemInterface

class UtilTest(unittest.TestCase):
    def test_tag_escape_sequences(self):
        result = list(util.tag_escape_sequences('now "is" the time; "the hour" has "come"', '"'))
        expected_result = [('now ', False), ('is', True), (' the time; ', False), ('the hour', True), (' has ', False), ('come', True), ('', False)]
        self.assertEqual(result, expected_result)
    
    def test_batch(self):
        result = list(util.batch("spamspam", 3))
        expected_result = [['s', 'p', 'a'], ['m', 's', 'p'], ['a', 'm']]
        self.assertEqual(result, expected_result)

    def test_find_non_substr(self):
        self.assertEqual(util.find_non_substr('steem'), 'a')
        self.assertEqual(util.find_non_substr('steemian'), 'b')
        self.assertEqual(util.find_non_substr('steemian bob'), 'c')
        self.assertEqual(util.find_non_substr('steemian bob can'), 'd')
        # skip 'e' because 'steem' contains 'e'
        self.assertEqual(util.find_non_substr('steemian bob can do'), 'f')
        self.assertEqual(util.find_non_substr('steemian bob can do fun'), 'g')
        self.assertEqual(util.find_non_substr('steemian bob can do fun things'), 'j')

    def test_iterate_operations_from(self):
        backend = SteemRemoteBackend(nodes=["https://api.steemit.com"], appbase=True)
        steemd = SteemInterface(backend)
        result = util.iterate_operations_from(steemd, True, 1102, 1103, set())
        expected_op = {
            'type': 'pow_operation',
            'value': {
                'worker_account': 'steemit11',
                'block_id': '0000044df0f062c0504a8e37288a371ada63a1c7',
                'nonce': 33097,
                'work': {
                    'worker': 'STM65wH1LZ7BfSHcK69SShnqCAH5xdoSZpGkUjmzHJ5GCuxEK9V5G',
                    'input': '45a3824498b87e41129f6fef17be276af6ff87d1e859128f28aaa9c08208871d',
                    'signature': '1f93a52c4f794803b2563845b05b485e3e5f4c075ddac8ea8cffb988a1ffcdd1055590a3d5206a3be83cab1ea548fc52889d43bdbd7b74d62f87fb8e2166145a5d',
                    'work': '00003e554a58830e7e01669796f40d1ce85c7eb979e376cb49e83319c2688c7e',
                }, 'props': {
                    'account_creation_fee': {"amount" : "100000", "precision" : 3, "nai" : "@@000000021"},
                    'maximum_block_size': 131072,
                    'sbd_interest_rate': 1000
                }
            }
        }
        
        # Scan all of the results and match against the expected op.  This will
        # fail if we get anything other than this exact op.
        for op in result:
            self.assertEqual(op['type'], expected_op['type'])
            self.assertEqual(op['value']['worker_account'], expected_op['value']['worker_account'])
            self.assertEqual(op['value']['block_id'], expected_op['value']['block_id'])
            self.assertEqual(op['value']['nonce'], expected_op['value']['nonce'])
            self.assertEqual(op['value']['work']['worker'], expected_op['value']['work']['worker'])
            self.assertEqual(op['value']['work']['input'], expected_op['value']['work']['input'])
            self.assertEqual(op['value']['work']['signature'], expected_op['value']['work']['signature'])
            self.assertEqual(op['value']['work']['work'], expected_op['value']['work']['work'])
            self.assertEqual(op['value']['props']['account_creation_fee']['amount'], expected_op['value']['props']['account_creation_fee']['amount'])
            self.assertEqual(op['value']['props']['account_creation_fee']['precision'], expected_op['value']['props']['account_creation_fee']['precision'])
            self.assertEqual(op['value']['props']['account_creation_fee']['nai'], expected_op['value']['props']['account_creation_fee']['nai'])
            self.assertEqual(op['value']['props']['maximum_block_size'], expected_op['value']['props']['maximum_block_size'])
            self.assertEqual(op['value']['props']['sbd_interest_rate'], expected_op['value']['props']['sbd_interest_rate'])

    def test_action_to_str(self):
        action = ["metadata", {}]
        result = util.action_to_str(action)
        self.assertEqual(result, '["metadata",{"esc":"b"}]')
