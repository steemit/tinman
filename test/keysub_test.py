import unittest
import json

from tinman import keysub

class KeysubTest(unittest.TestCase):
    def test_process_esc(self):
        # Note, resolver needs to be mocked to properly test.
        self.assertRaises(AttributeError, keysub.process_esc, 'Bpublickey:owner-initminerB', 'B')
    
    def test_process_esc_ignored(self):
        result = keysub.process_esc('foo:bar', 'baz')
        expected_result = 'foo:bar'
        self.assertEqual(result, expected_result)

    def test_compute_keypair_from_seed(self):
        # Note, resolver needs to be mocked to properly test.
        self.assertRaises(FileNotFoundError, keysub.compute_keypair_from_seed, '1234', 'secret')
        self.assertRaises(json.decoder.JSONDecodeError, keysub.compute_keypair_from_seed, '1234', 'secret', '/usr/bin/true')
