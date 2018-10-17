import unittest
import json
import shutil

from tinman import prefixsub

class PrefixsubTest(unittest.TestCase):
    def test_transform_prefix_str(self):
        object = "STM6LLegbAgLAy28EHrffBVuANFWcFgmqRMW13wBmTExqFE9SCkg4"
        result = prefixsub.transform_prefix(object)
        expected_result = "TST6LLegbAgLAy28EHrffBVuANFWcFgmqRMW13wBmTExqFE9SCkg4"
        self.assertEqual(result, expected_result)

    def test_transform_prefix_str_wrong_length(self):
        object = "STM6LLeg"
        result = prefixsub.transform_prefix(object)
        expected_result = "STM6LLeg"
        self.assertEqual(result, expected_result)

    def test_transform_prefix_list(self):
        object = ["STM6LLegbAgLAy28EHrffBVuANFWcFgmqRMW13wBmTExqFE9SCkg4"]
        prefixsub.transform_prefix(object)
        expected_result = ["TST6LLegbAgLAy28EHrffBVuANFWcFgmqRMW13wBmTExqFE9SCkg4"]
        self.assertEqual(object, expected_result)

    def test_transform_prefix_dict(self):
        object = {"public_key": "STM6LLegbAgLAy28EHrffBVuANFWcFgmqRMW13wBmTExqFE9SCkg4"}
        prefixsub.transform_prefix(object)
        expected_result = {"public_key": "TST6LLegbAgLAy28EHrffBVuANFWcFgmqRMW13wBmTExqFE9SCkg4"}
        self.assertEqual(object, expected_result)

    def test_transform_prefix_trivial_account_update_operation(self):
        object = {
           "account":"alice",
           "json_metadata":"{\"profile\":{\"about\":\"Curiousness\",\"location\":\"Wonderland\",\"name\":\"Alice\"}}",
           "memo_key":"STM6XzTJphLvDCifPvmQ2WtUWxgQk9AZiFEMucPiTKikJCNMZabAq"
        }
        prefixsub.transform_prefix(object)
        expected_result = {
           "account":"alice",
           "json_metadata":"{\"profile\":{\"about\":\"Curiousness\",\"location\":\"Wonderland\",\"name\":\"Alice\"}}",
           "memo_key":"TST6XzTJphLvDCifPvmQ2WtUWxgQk9AZiFEMucPiTKikJCNMZabAq"
        }
        self.assertEqual(object, expected_result)

    def test_transform_prefix_complex_account_update_operation(self):
        """
        Note, this test contains a public key pattern in the json_metadata field
        which should be ignored for the test to pass.
        """
        
        object = {
           "account":"bob",
           "active":{
              "account_auths":[],
              "key_auths":[["STM714aBC2zNkqfrrWSC1dVnZKPeFiXZg4RAHPRNzdr7Asue3mtnF", 1]],
              "weight_threshold":1
           },
           "json_metadata":"{\"profile\":{\"cover_image\":\"https://imgur.org/STM714aBC2zNkqfrrWSC1dVnZKPeFiXZg4RAHPRNzdr7Asue3mtnF.jpg\"}}",
           "memo_key":"STM5AjkXufK1oDPNqRVyLoj3uYoHTnwyP1pcbKCZGkRLscSToh2xV",
           "owner":{
              "account_auths":[],
              "key_auths":[["STM8QVEwTJG6NZuhZcR8fT66yKAfYG6ep8hT8eTLgAGMaq2RXPVCW", 1]],
              "weight_threshold":1
           },
           "posting":{
              "account_auths":[
                 ["alice", 1],
                 ["charlie", 1]
              ],
              "key_auths":[["STM7vBuapLzXVi9qo9vu8VUD2YieNTZ6w8iMjGUGf2j3eePYA2Y5k", 1]],
              "weight_threshold":1
           }
        }
        prefixsub.transform_prefix(object)
        expected_result = {
           "account":"bob",
           "active":{
              "account_auths":[],
              "key_auths":[["TST714aBC2zNkqfrrWSC1dVnZKPeFiXZg4RAHPRNzdr7Asue3mtnF", 1]],
              "weight_threshold":1
           },
           "json_metadata":"{\"profile\":{\"cover_image\":\"https://imgur.org/STM714aBC2zNkqfrrWSC1dVnZKPeFiXZg4RAHPRNzdr7Asue3mtnF.jpg\"}}",
           "memo_key":"TST5AjkXufK1oDPNqRVyLoj3uYoHTnwyP1pcbKCZGkRLscSToh2xV",
           "owner":{
              "account_auths":[],
              "key_auths":[["TST8QVEwTJG6NZuhZcR8fT66yKAfYG6ep8hT8eTLgAGMaq2RXPVCW", 1]],
              "weight_threshold":1
           },
           "posting":{
              "account_auths":[
                 ["alice", 1],
                 ["charlie", 1]
              ],
              "key_auths":[["TST7vBuapLzXVi9qo9vu8VUD2YieNTZ6w8iMjGUGf2j3eePYA2Y5k", 1]],
              "weight_threshold":1
           }
        }
        self.assertEqual(object, expected_result)
