import unittest
import json
import shutil

from tinman import keysub

class KeysubTest(unittest.TestCase):
    def test_process_esc(self):
        self.assertRaises(AttributeError, keysub.process_esc, 'Bpublickey:owner-initminerB', 'B')
    
    def test_process_esc_ignored(self):
        result = keysub.process_esc('foo:bar', 'baz')
        expected_result = 'foo:bar'
        self.assertEqual(result, expected_result)

    def test_compute_keypair_from_seed(self):
        try:
            # Try in case the binary is in the path environment.
            result = keysub.compute_keypair_from_seed('1234', 'secret')
            expected_result = "('TST6n6jNUngRVCkh3GKBEZVe6r8reBPHmi8bRkwFZ1yh83iKfGcSN', '5JFQtrsidduA79M523UZ2yKub4383BUykWthPkmTD2TAiVfDrA6')"
            self.assertEqual(result, expected_result)
        except FileNotFoundError:
            # Note, resolver needs to be mocked to properly test.
            true_exe = shutil.which("true")
            self.assertRaises(json.decoder.JSONDecodeError, keysub.compute_keypair_from_seed, '1234', 'secret', true_exe)
