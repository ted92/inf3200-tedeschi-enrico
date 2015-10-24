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
        receiver = ncore.NodeDescriptor(host_port="localhost:8000")
        req = nhttp.HttpRequest(
                destination = receiver,
                method = "POST",
                path = "join",
                body = "localhost:8001\n")

        msg = nhttp.parse_request(req)

        self.assertEqual(isinstance(msg, ncore.Join), True)
        self.assertEqual(msg.destination, receiver)
        self.assertEqual(msg.new_node,
                ncore.NodeDescriptor(host_port="localhost:8001"))


    def test_build_join_accept(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.JoinAccepted(destination=d1, successor=d0)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "POST")
        self.assertEqual(req.path, "join/accepted")
        self.assertEqual(req.body, "localhost:8000")

    def test_parse_join_accept(self):
        receiver = ncore.NodeDescriptor(host_port="localhost:8001")
        req = nhttp.HttpRequest(
                destination = receiver,
                method = "POST",
                path = "join/accepted",
                body = "localhost:8000\n")

        msg = nhttp.parse_request(req)

        self.assertEqual(isinstance(msg, ncore.JoinAccepted), True)
        self.assertEqual(msg.destination, receiver)
        self.assertEqual(msg.successor,
                ncore.NodeDescriptor(host_port="localhost:8000"))


if __name__ == '__main__':
    unittest.main()
