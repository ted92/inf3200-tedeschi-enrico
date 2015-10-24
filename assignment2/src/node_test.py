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

    def test_ip_port(self):
        nd = node.NodeDescriptor("127.0.0.1", "8000")
        self.assertEqual(nd.ip_port, "127.0.0.1:8000")

    def test_rank(self):
        nd = node.NodeDescriptor(ip_port="127.0.0.1:8000")
        self.assertEqual(nd.rank, node.node_hash("127.0.0.1:8000"))
        self.assertEqual(nd.rank, 102808487155392830909659332955855849052L)


def key_ranked(*args):
    modulus = args[0]
    long_max_digit = 100000000000000000000000000000000000000L
    TRIES_LIMIT=1000
    for i in range(0, TRIES_LIMIT):
        key = str(i)
        if (node.node_hash(key) / long_max_digit == modulus):
            return key
    raise Exception("Could not generate an appropriate key")

def node_ranked(rank):
    desc = node.NodeDescriptor(ip="127.0.0.1", port=rank)
    long_max_digit = 100000000000000000000000000000000000000L
    desc.rank = rank * long_max_digit
    return desc


class TestNodeCore(unittest.TestCase):

    def test_responsible_for_key_not_found(self):
        node_core = node.NodeCore(desc=node_ranked(0), successor=node_ranked(1))
        key = key_ranked(0)
        self.assertEqual(node_core.responsible_for_key(key), True)

    def test_responsible_for_key_negative(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = key_ranked(1, node_count)

        node_core = node.NodeCore(node_count, rank, next_node)
        self.assertEqual(node_core.responsible_for_key(key), False)


    def test_not_responsible_put(self):
        current =node_ranked(0)
        successor = node_ranked(1)
        node_core = node.NodeCore(desc=current, successor=successor)

        key = key_ranked(1)
        value = "THIS IS A TEST VALUE"

        # put value
        result = node_core.do_put(key,value)
        self.assertEqual(isinstance(result, node.ForwardRequest), True,
            "Expected ForwardRequest, got " + pformat(result))
        self.assertEqual(result.destination, successor)


    def test_not_responsible_get(self):
        current = node_ranked(0)
        successor = node_ranked(1)
        node_core = node.NodeCore(desc=current, successor=successor)

        key = key_ranked(1)
        value = "THIS IS A TEST VALUE"

        # put value
        result = node_core.do_get(key)
        self.assertEqual(isinstance(result, node.ForwardRequest), True,
            "Expected ForwardRequest, got " + pformat(result))
        self.assertEqual(result.destination, successor)


    def test_responsible_put_get(self):
        node_count = 5
        rank = 0
        next_node = "NEXT"
        key = key_ranked(rank, node_count)
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
        key = key_ranked(rank, node_count)

        node_core = node.NodeCore(node_count, rank, next_node)
        result = node_core.do_get(key)

        self.assertEqual(isinstance(result, node.ValueNotFound), True,
            "Expected ValueNotFound, got " + pformat(result))



    def test_ring_config_linear(self):
        d0 = node_ranked(0)
        d1 = node_ranked(1)
        d2 = node_ranked(2)

        node0 = node.NodeCore(desc=d0, successor=d1)
        node1 = node.NodeCore(desc=d1, successor=d2)
        node2 = node.NodeCore(desc=d2, successor=d0)

        key = key_ranked(2)
        value = "THIS IS A TEST VALUE"

        result = node0.do_put(key,value)
        self.assertEqual(result.destination, d1)

        result = node1.do_put(key,value)
        self.assertEqual(result.destination, d2)

        result = node2.do_put(key,value)
        self.assertEqual(isinstance(result, node.ValueStored), True)


    def test_ring_config_wrap_around(self):
        d0 = node_ranked(0)
        d1 = node_ranked(1)
        d2 = node_ranked(2)

        node0 = node.NodeCore(desc=d0, successor=d1)
        node1 = node.NodeCore(desc=d1, successor=d2)
        node2 = node.NodeCore(desc=d2, successor=d0)

        key = key_ranked(0)
        value = "THIS IS A TEST VALUE"

        result = node1.do_put(key,value)
        self.assertEqual(result.destination, d2)

        result = node2.do_put(key,value)
        self.assertEqual(result.destination, d0)

        result = node0.do_put(key,value)
        self.assertEqual(isinstance(result, node.ValueStored), True)


    def test_single_node(self):
        d0 = node_ranked(0)

        node0 = node.NodeCore(desc=d0)

        key = key_ranked(1)
        value = "TEST VALUE"

        result = node0.do_put(key,value)
        self.assertEqual(isinstance(result, node.ValueStored), True)



if __name__ == '__main__':
    unittest.main()
