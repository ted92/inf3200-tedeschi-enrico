#!/usr/bin/python
# vim: set sts=4 sw=4 et:

import unittest
import node
from pprint import pformat

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


class TestNodeDescriptor(unittest.TestCase):

    def test_construct(self):
        nd = node.NodeDescriptor(ip="127.0.0.1", port="8000")
        self.assertEqual(nd.ip, "127.0.0.1")
        self.assertEqual(nd.port, "8000")

    def test_parse(self):
        nd = node.NodeDescriptor(ip_port="127.0.0.1:8000")
        self.assertEqual(nd.ip, "127.0.0.1")
        self.assertEqual(nd.port, "8000")

    def test_bad_construct(self):
        self.assertRaises(RuntimeError, node.NodeDescriptor)

    def test_string(self):
        nd = node.NodeDescriptor("127.0.0.1", "8000")
        self.assertEqual(str(nd), "127.0.0.1:8000")

    def test_rank(self):
        nd = node.NodeDescriptor(ip_port="127.0.0.1:8000")
        self.assertEqual(nd.rank, node.node_hash("127.0.0.1:8000"))
        self.assertEqual(nd.rank, 102808487155392830909659332955855849052L)


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

    def test_responsible_for_key_not_found(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = find_key_with_modulus(rank, node_count)

        node_core = node.NodeCore(node_count, rank, next_node)
        self.assertEqual(node_core.responsible_for_key(key), True)

    def test_responsible_for_key_negative(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = find_key_with_modulus(1, node_count)

        node_core = node.NodeCore(node_count, rank, next_node)
        self.assertEqual(node_core.responsible_for_key(key), False)


    def test_not_responsible_put(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = find_key_with_modulus(1, node_count)
        value = "THIS IS A TEST VALUE"

        node_core = node.NodeCore(node_count, rank, next_node)

        # put value
        result = node_core.do_put(key,value)
        self.assertEqual(isinstance(result, node.ForwardRequest), True,
            "Expected ForwardRequest, got " + pformat(result))
        self.assertEqual(result.destination, "NEXT")


    def test_not_responsible_get(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = find_key_with_modulus(1, node_count)
        value = "THIS IS A TEST VALUE"

        node_core = node.NodeCore(node_count, rank, next_node)

        # put value
        result = node_core.do_get(key)
        self.assertEqual(isinstance(result, node.ForwardRequest), True,
            "Expected ForwardRequest, got " + pformat(result))
        self.assertEqual(result.destination, "NEXT")


    def test_responsible_put_get(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = find_key_with_modulus(rank, node_count)
        value = "THIS IS A TEST VALUE"

        node_core = node.NodeCore(node_count, rank, next_node)

        # put value
        result = node_core.do_put(key,value)
        self.assertEqual(isinstance(result, node.ValueStored), True,
            "Expected ValueStored, got " + pformat(result))

        # get value
        result = node_core.do_get(key)
        self.assertEqual(isinstance(result, node.ValueFound), True,
            "Expected ValueFound, got " + pformat(result))
        self.assertEqual(result.value, value)


    def test_responsible_but_not_found(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = find_key_with_modulus(rank, node_count)

        node_core = node.NodeCore(node_count, rank, next_node)
        result = node_core.do_get(key)

        self.assertEqual(isinstance(result, node.ValueNotFound), True,
            "Expected ValueNotFound, got " + pformat(result))



    def test_ring_config_linear(self):
        node0 = node.NodeCore(3, 0, 'node1')
        node1 = node.NodeCore(3, 1, 'node2')
        node2 = node.NodeCore(3, 2, 'node0')

        key = find_key_with_modulus(2, 3)
        value = "THIS IS A TEST VALUE"

        result = node0.do_put(key,value)
        self.assertEqual(result.destination, "node1")

        result = node1.do_put(key,value)
        self.assertEqual(result.destination, "node2")

        result = node2.do_put(key,value)
        self.assertEqual(isinstance(result, node.ValueStored), True)


    def test_ring_config_wrap_around(self):
        node0 = node.NodeCore(3, 0, 'node1')
        node1 = node.NodeCore(3, 1, 'node2')
        node2 = node.NodeCore(3, 2, 'node0')

        key = find_key_with_modulus(0, 3)
        value = "THIS IS A TEST VALUE"

        result = node1.do_put(key,value)
        self.assertEqual(result.destination, "node2")

        result = node2.do_put(key,value)
        self.assertEqual(result.destination, "node0")

        result = node0.do_put(key,value)
        self.assertEqual(isinstance(result, node.ValueStored), True)




if __name__ == '__main__':
    unittest.main()
