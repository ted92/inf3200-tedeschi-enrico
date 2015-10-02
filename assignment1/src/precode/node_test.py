#!/usr/bin/python
# vim: set sts=4 sw=4 et:

import unittest
import node

class TestNodeHashing(unittest.TestCase):

    def test_node_hash_to_number(self):
        numeric_hash = node.node_hash("hello world!")
        self.assertTrue(isinstance(numeric_hash, (int,long)),
            "Expected hash to be numeric (int or long). Got %s: '%s'" %
                (type(numeric_hash), numeric_hash) )

    def test_node_hash_same_string_same_hash(self):
        hash_a = node.node_hash("hello world!")
        hash_b = node.node_hash("hello"+ " world!")
        self.assertEqual(hash_a, hash_b)



def hash_modulus(key, node_count):
    return node.node_hash(key) % node_count

def find_key_with_modulus(modulus, count):
    TRIES_LIMIT=1000
    for i in range(0, TRIES_LIMIT):
        key = str(i)
        if (node.node_hash(key) % count == modulus):
            return key
    raise Exception("Could not generate an appropriate key")


class TestNodeCore(unittest.TestCase):

    def test_responsible_for_key_positive(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = find_key_with_modulus(rank, node_count)

        node_core = node.Node(node_count, rank, next_node)
        self.assertEqual(node_core.responsible_for_key(key), True)

    def test_responsible_for_key_negative(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = find_key_with_modulus(1, node_count)

        node_core = node.Node(node_count, rank, next_node)
        self.assertEqual(node_core.responsible_for_key(key), False)


if __name__ == '__main__':
    unittest.main()
