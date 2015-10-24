#!/usr/bin/env python

import unittest
from pprint import pformat

import node_core2 as node

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
        nd = node.NodeDescriptor(host="127.0.0.1", port="8000")
        self.assertEqual(nd.host, "127.0.0.1")
        self.assertEqual(nd.port, "8000")

    def test_parse(self):
        nd = node.NodeDescriptor(host_port="127.0.0.1:8000")
        self.assertEqual(nd.host, "127.0.0.1")
        self.assertEqual(nd.port, "8000")

    def test_bad_construct(self):
        self.assertRaises(RuntimeError, node.NodeDescriptor)

    def test_host_port(self):
        nd = node.NodeDescriptor("127.0.0.1", "8000")
        self.assertEqual(nd.host_port, "127.0.0.1:8000")

    def test_rank(self):
        nd = node.NodeDescriptor(host_port="127.0.0.1:8000")
        self.assertEqual(nd.rank, node.node_hash("127.0.0.1:8000"))
        self.assertEqual(nd.rank, 102808487155392830909659332955855849052L)


long_max_digit = 100000000000000000000000000000000000000L

def key_ranked(*args):
    modulus = args[0]
    TRIES_LIMIT=1000
    for i in range(0, TRIES_LIMIT):
        key = str(i)
        if (node.node_hash(key) / long_max_digit == modulus):
            return key
    raise Exception("Could not generate an appropriate key")

def node_ranked(rank):
    desc = node.NodeDescriptor(host="127.0.0.1", port=rank)
    desc.rank = rank * long_max_digit
    return desc

class TestNodeCore(unittest.TestCase):

    def test_single_node_no_successor(self):
        d0 = node_ranked(0);    n0 = node.NodeCore(d0)
        self.assertEqual(n0.descriptor, d0)
        self.assertEqual(n0.successor, None)

    def test_single_always_responsible_for_key(self):
        d0 = node_ranked(0);    n0 = node.NodeCore(d0)
        k1 = key_ranked(1)
        self.assertEqual(n0.responsible_for_key(k1), True)

    def test_join_single(self):
        d0 = node_ranked(0);    n0 = node.NodeCore(d0)
        d1 = node_ranked(1);    n1 = node.NodeCore(d1)

        # Join nodes 0 and 1
        result = n0.handle_message(node.Join(destination=d0, new_node=d1))
        msg = result[0]

        # Original node should accept the message
        self.assertEqual(isinstance(msg, node.JoinAccepted), True)
        self.assertEqual(msg.successor, d0)

        # Original node should accept new node as its successor
        self.assertEqual(n0.successor, d1)

        # New node should take existing node as its successor
        n1.handle_message(msg)
        self.assertEqual(n1.successor, d0)

    def test_not_responsible_for_key(self):
        d0 = node_ranked(0);    n0 = node.NodeCore(d0)
        d1 = node_ranked(1);    n1 = node.NodeCore(d1)

        # Join nodes 0 and 1
        result = n0.handle_message(node.Join(d0,d1))
        msg = result[0]
        n1.handle_message(msg)

        k1 = key_ranked(1)
        self.assertEqual(n0.responsible_for_key(k1), False)
        self.assertEqual(n1.responsible_for_key(k1), True)

    def test_join_double_direct(self):
        d0 = node_ranked(0);    n0 = node.NodeCore(d0)
        d1 = node_ranked(1);    n1 = node.NodeCore(d1)
        d2 = node_ranked(2);    n2 = node.NodeCore(d2)

        # Join nodes 0 and 1
        result = n0.handle_message(node.Join(d0, d1))
        msg = result[0]
        n1.handle_message(msg)

        # Add node 2 at 1
        result = n1.handle_message(node.Join(d1, d2))
        msg = result[0]

        # Node 1 should accept the message
        self.assertEqual(isinstance(msg, node.JoinAccepted), True)
        self.assertEqual(msg.successor, d0)

        # Node 1 should accept node 2 as its new successor
        self.assertEqual(n1.successor, d2)

        # New node (2) should take the given node as its successor
        n2.handle_message(msg)
        self.assertEqual(n2.successor, d0)

'''
    def test_join_double_indirect(self):
        d0 = node_ranked(0);    n0 = node.NodeCore(d0)
        d1 = node_ranked(1);    n1 = node.NodeCore(d1)
        d2 = node_ranked(2);    n2 = node.NodeCore(d2)

        # Join nodes 0 and 1
        result = n0.handle_request(node.Join(d1))
        n1.handle_request(result)

        # Add node 2 at 0
        fwd = n0.handle_request(node.Join(d2))

        # Node 0 should forward the request
        self.assertEqual(isinstance(fwd, node.ForwardRequest), True)
        self.assertEqual(fwd.destination, d1)

        # Deliver forward request
        result = n1.handle_request(fwd.request)

        # Node 1 should accept the request
        self.assertEqual(isinstance(result, node.JoinAccepted), True)
        self.assertEqual(result.successor, d0)

        # Node 1 should accept node 2 as its new successor
        self.assertEqual(n1.successor, d2)

        # New node (2) should take the given node as its successor
        n2.handle_request(result)
        self.assertEqual(n2.successor, d0)
'''''


if __name__ == '__main__':
    unittest.main()
