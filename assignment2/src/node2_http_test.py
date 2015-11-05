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

    def test_split_empty(self):
        s = "\n".strip()
        self.assertEqual(s, "")

        l = "".split("\n")
        self.assertEqual(l, [''])

    def test_node_descriptor_list_empty(self):
        l = nhttp.parse_node_descriptor_list("\n")
        self.assertEqual(l, [])

    def test_node_descriptor_list_single(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        l = nhttp.parse_node_descriptor_list("localhost:8000\n")
        self.assertEqual(l, [d0])

    def test_node_descriptor_list_double(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        l = nhttp.parse_node_descriptor_list("localhost:8000\nlocalhost:8001\n")
        self.assertEqual(l, [d0,d1])

    def test_build_join(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.Join(destination=d0, new_node=d1)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "POST")
        self.assertEqual(req.path, "/join")
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
        d3 = ncore.NodeDescriptor(host_port="localhost:8003")
        msg = ncore.JoinAccepted(destination=d1, successor=d2, predecessor=d0, leader=d3)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "POST")
        self.assertEqual(req.path, "/join/accepted")
        self.assertEqual(req.body,
                "successor = localhost:8002\npredecessor = localhost:8000\nleader = localhost:8003\n")

    def test_parse_join_accept(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        d2 = ncore.NodeDescriptor(host_port="localhost:8002")
        d3 = ncore.NodeDescriptor(host_port="localhost:8003")
        msg = ncore.JoinAccepted(destination=d1, successor=d2, predecessor=d0, leader=d3)

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)

    def test_build_new_predecessor(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.NewPredecessor(destination=d1, predecessor=d0)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "PUT")
        self.assertEqual(req.path, "/predecessor")
        self.assertEqual(req.body, "localhost:8000")

    def test_parse_new_predecessor(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.NewPredecessor(destination=d1, predecessor=d0)

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)

    def test_build_new_successor(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.NewSuccessor(destination=d1, successor=d0)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "PUT")
        self.assertEqual(req.path, "/successor")
        self.assertEqual(req.body, "localhost:8000")

    def test_parse_new_successor(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.NewSuccessor(destination=d1, successor=d0)

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)

    def test_build_get_neighbors(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        msg = ncore.GetNeighbors(destination=d0)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "GET")
        self.assertEqual(req.path, "/getNodes")
        self.assertEqual(req.body, "")

    def test_parse_get_neighbors(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        msg = ncore.GetNeighbors(destination=d0)

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)

    def test_build_get_leader(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        msg = ncore.GetLeader(destination=d0)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "GET")
        self.assertEqual(req.path, "/getCurrentLeader")
        self.assertEqual(req.body, "")

    def test_parse_get_leader(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        msg = ncore.GetLeader(destination=d0)

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)

    def test_build_election(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.Election(destination=d0, participants=[d0,d1])

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "POST")
        self.assertEqual(req.path, "/election")
        self.assertEqual(req.body, "localhost:8000\nlocalhost:8001")

    def test_parse_election(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.Election(destination=d0, participants=[d0,d1])

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)

    def test_build_election_result(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.ElectionResult(destination=d0, new_leader=d1)

        req = nhttp.build_request(msg)

        self.assertEqual(req.method, "POST")
        self.assertEqual(req.path, "/election/result")
        self.assertEqual(req.body, "localhost:8001")

    def test_parse_election_result(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        msg = ncore.ElectionResult(destination=d0, new_leader=d1)

        req = nhttp.build_request(msg)
        parsed = nhttp.parse_request(req)
        self.assertEqual(parsed, msg)

    def test_build_generic_ok(self):
        dr = ncore.GenericOk()

        resp = nhttp.build_response(dr)

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body, "")

    def test_build_node_list(self):
        d0 = ncore.NodeDescriptor(host_port="localhost:8000")
        d1 = ncore.NodeDescriptor(host_port="localhost:8001")
        d2 = ncore.NodeDescriptor(host_port="localhost:8002")
        dr = ncore.NodeList(nodes=[d0,d1,d2])

        resp = nhttp.build_response(dr)

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body, "localhost:8000\nlocalhost:8001\nlocalhost:8002")

    def test_http_request_no_slash(self):
        hr = nhttp.HttpRequest(method="GET", path="needs-a-slash")
        self.assertEqual(hr.path, "/needs-a-slash")

if __name__ == '__main__':
    unittest.main()
