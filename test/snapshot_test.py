import unittest
import json
import shutil

from tinman import snapshot
from simple_steem_client.client import SteemRemoteBackend, SteemInterface, SteemRPCException

class SnapshotTest(unittest.TestCase):
    def test_list_all_accounts(self):
        backend = SteemRemoteBackend(nodes=["http://test.com"], appbase=True)
        steemd = SteemInterface(backend)
        self.assertIsNotNone(snapshot.list_all_accounts(steemd))
