#!/usr/bin/env python

import unittest
from pprint import pformat

import node_core2 as ncore
import node2_http as nhttp

long_max_digit = 100000000000000000000000000000000000000L

def node_ranked(rank):
    desc = ncore.NodeDescriptor(host="127.0.0.1", port=rank)
    desc.rank = rank * long_max_digit
    return desc

class TestParseBuild(unittest.TestCase):

    def test_build_join(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.Join(destination=d0, new_node=d1)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "POST")
        self.assertEqual(req.path, "join")
        self.assertEqual(req.body, "localhost:8001")

    def test_parse_join(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.Join(destination=d0, new_node=d1)

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)


    def test_build_join_accept(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        d2 = ncore.NodeDescriptor(host_port="localhost:8002")
        msg = ncore.JoinAccepted(destination=d1, successor=d2, predecessor=d0)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "POST")
        self.assertEqual(req.path, "join/accepted")
        self.assertEqual(req.body,
                "successor = localhost:8002\npredecessor = localhost:8000\n")

    def test_parse_join_accept(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        d2 = ncore.NodeDescriptor(host_port="localhost:8002")
        msg = ncore.JoinAccepted(destination=d1, successor=d2, predecessor=d0)

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)

    def test_build_new_predecessor(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.NewPredecessor(destination=d1, predecessor=d0)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "PUT")
        self.assertEqual(req.path, "predecessor")
        self.assertEqual(req.body, "localhost:8000")

    def test_parse_new_predecessor(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.NewPredecessor(destination=d1, predecessor=d0)

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)


if __name__ == '__main__':
    unittest.main()
