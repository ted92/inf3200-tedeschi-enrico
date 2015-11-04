#!/usr/bin/env python

import logging
import unittest
from pprint import pformat

import node_core2 as ncore

class TestNodeHashing(unittest.TestCase):

    def test_node_hash_to_number(self):
        numeric_hash = ncore.node_hash("hello world!")
        self.assertTrue(isinstance(numeric_hash, (int,long)),
            "Expected hash to be numeric (int or long). Got %s: '%s'" %
                (type(numeric_hash), numeric_hash) )

    def test_node_hash_same_string_same_hash(self):
        hash_a = ncore.node_hash("hello world!")
        hash_b = ncore.node_hash("hello"+ " world!")
        self.assertEqual(hash_a, hash_b)

class TestNodeDescriptor(unittest.TestCase):

    def test_construct(self):
        nd = ncore.NodeDescriptor(host="127.0.0.1", port="8000")
        self.assertEqual(nd.host, "127.0.0.1")
        self.assertEqual(nd.port, 8000)

    def test_parse(self):
        nd = ncore.NodeDescriptor(host_port="127.0.0.1:8000")
        self.assertEqual(nd.host, "127.0.0.1")
        self.assertEqual(nd.port, 8000)

    def test_parse_trim(self):
        nd = ncore.NodeDescriptor(host_port="\t\t  127.0.0.1:8000  \n")
        self.assertEqual(nd.host, "127.0.0.1")
        self.assertEqual(nd.port, 8000)
        self.assertEqual(nd.host_port, "127.0.0.1:8000")

    def test_bad_construct(self):
        self.assertRaises(RuntimeError, ncore.NodeDescriptor)

    def test_host_port(self):
        nd = ncore.NodeDescriptor("127.0.0.1", "8000")
        self.assertEqual(nd.host, "127.0.0.1")
        self.assertEqual(nd.port, 8000)
        self.assertEqual(nd.host_port, "127.0.0.1:8000")

    def test_host_port_trim(self):
        nd = ncore.NodeDescriptor("\t 127.0.0.1  \n", "\t 8000 \n")
        self.assertEqual(nd.host, "127.0.0.1")
        self.assertEqual(nd.port, 8000)
        self.assertEqual(nd.host_port, "127.0.0.1:8000")

    def test_rank(self):
        nd = ncore.NodeDescriptor(host_port="127.0.0.1:8000")
        self.assertEqual(nd.rank, ncore.node_hash("127.0.0.1:8000"))
        self.assertEqual(nd.rank, 102808487155392830909659332955855849052L)

    def test_equal_a_b_true(self):
        d0 = ncore.NodeDescriptor(host_port="127.0.0.1:8000")
        d1 = ncore.NodeDescriptor(host_port="127.0.0.1:8000")
        self.assertEqual(d0,d1)

    def test_equal_a_b_different_host(self):
        d0 = ncore.NodeDescriptor(host_port="127.0.0.1:8000")
        d1 = ncore.NodeDescriptor(host_port="127.0.0.2:8000")
        self.assertNotEqual(d0,d1)

    def test_equal_a_b_different_port(self):
        d0 = ncore.NodeDescriptor(host_port="127.0.0.1:8000")
        d1 = ncore.NodeDescriptor(host_port="127.0.0.1:8001")
        self.assertNotEqual(d0,d1)

    def test_equal_a_b_aNone(self):
        d0 = None
        d1 = ncore.NodeDescriptor(host_port="127.0.0.1:8000")
        self.assertNotEqual(d0,d1)
        self.assertEqual(None, d0)

    def test_equal_a_b_bNone(self):
        d0 = ncore.NodeDescriptor(host_port="127.0.0.1:8000")
        d1 = None
        self.assertNotEqual(d0,d1)
        self.assertEqual(d1, None)

long_max_digit = 100000000000000000000000000000000000000L

def key_ranked(*args):
    modulus = args[0]
    TRIES_LIMIT=1000
    for i in range(0, TRIES_LIMIT):
        key = str(i)
        if (ncore.node_hash(key) / long_max_digit == modulus):
            return key
    raise Exception("Could not generate an appropriate key")

def node_ranked(rank):
    desc = ncore.NodeDescriptor(host="127.0.0.1", port=rank)
    desc.rank = rank * long_max_digit
    return desc

class TestNodeCore(unittest.TestCase):

    def setUp(self):
        self.saved_log_level = ncore.logger.level
        ncore.logger.setLevel(logging.CRITICAL)

    def tearDown(self):
        ncore.logger.setLevel(self.saved_log_level)

    def test_single_node_no_successor(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        self.assertEqual(n0.descriptor, d0)
        self.assertEqual(n0.successor, None)
        self.assertEqual(n0.predecessor, None)

    def test_single_always_responsible_for_key(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        k1 = key_ranked(1)
        self.assertEqual(n0.responsible_for_key(k1), True)

    def assertDeepEqual(self, response, msg_list):
        if response != msg_list:
            raise AssertionError("""
                Expected: %s
                Got:      %s
            """ % (pformat(msg_list), pformat(response)) )

    def test_join_single(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)

        # Join nodes 0 and 1
        result = n0.handle_message(ncore.Join(destination=d0, new_node=d1))

        self.assertDeepEqual(
                result,
                ncore.GenericOk([
                    ncore.JoinAccepted(
                        destination=d1, successor=d0, predecessor=d0, leader=d0 )
                    ]))

        accept_msg = result.new_messages[0]

        # Original node should accept new node as its successor and predecessor
        self.assertEqual(n0.successor, d1)
        self.assertEqual(n0.predecessor, d1)

        # New node should take existing node as its successor and predecessor
        n1.handle_message(accept_msg)
        self.assertEqual(n1.successor, d0)
        self.assertEqual(n1.predecessor, d0)

    def test_not_responsible_for_key(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)

        # Join nodes 0 and 1
        result = n0.handle_message(ncore.Join(d0,d1))
        self.assertDeepEqual(
                result,
                ncore.GenericOk([
                    ncore.JoinAccepted(
                        destination=d1, successor=d0, predecessor=d0, leader=d0)
                    ]))

        accept_msg = result.new_messages[0]
        n1.handle_message(accept_msg)

        k1 = key_ranked(1)
        self.assertEqual(n0.responsible_for_key(k1), False)
        self.assertEqual(n1.responsible_for_key(k1), True)

    def test_join_double_direct(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)
        d2 = node_ranked(2);    n2 = ncore.NodeCore(d2)

        # Join nodes 0 and 1
        result = n0.handle_message(ncore.Join(d0, d1))
        accept_msg = result.new_messages[0]
        n1.handle_message(accept_msg)

        # Add node 2 at 1
        result = n1.handle_message(ncore.Join(d1, d2))
        self.assertDeepEqual(
                result,
                ncore.GenericOk([
                    ncore.NewPredecessor( destination=d0, predecessor=d2 ),
                    ncore.JoinAccepted(
                        destination=d2, successor=d0, predecessor=d1, leader=d0)
                    ]))

        newpred_msg = result.new_messages[0]
        accept_msg = result.new_messages[1]

        # Node 1 should accept node 2 as its new successor
        self.assertEqual(n1.successor, d2)

        # Successor should take the new node as its new predecessor
        n0.handle_message(newpred_msg)
        self.assertEqual(n0.predecessor, d2)

        # New node (2) should take the given nodes as successor and predecessor
        n2.handle_message(accept_msg)
        self.assertEqual(n2.successor, d0)
        self.assertEqual(n2.predecessor, d1)

    def test_join_double_indirect(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)
        d2 = node_ranked(2);    n2 = ncore.NodeCore(d2)

        # Join nodes 0 and 1
        result = n0.handle_message(ncore.Join(d0, d1))
        accept_msg = result.new_messages[0]
        n1.handle_message(accept_msg)

        # Add node 2 at 0
        result = n0.handle_message(ncore.Join(d0, d2))

        # Node 0 should forward the request
        self.assertDeepEqual(
                result,
                ncore.GenericOk([
                    ncore.Join(destination=d1, new_node=d2)
                    ]))
        fwd_join = result.new_messages[0]

        # Deliver forward request
        result = n1.handle_message(fwd_join)

        # Node 1 should accept the request
        self.assertDeepEqual(
                result,
                ncore.GenericOk([
                    ncore.NewPredecessor( destination=d0, predecessor=d2 ),
                    ncore.JoinAccepted(
                        destination=d2, successor=d0, predecessor=d1, leader=d0 )
                    ]))

        newpred_msg = result.new_messages[0]
        accept_msg = result.new_messages[1]

        # Node 1 should accept node 2 as its new successor
        self.assertEqual(n1.successor, d2)

        # Successor should take the new node as its new predecessor
        n0.handle_message(newpred_msg)
        self.assertEqual(n0.predecessor, d2)

        # New node (2) should take the given nodes as successor and predecessor
        n2.handle_message(accept_msg)
        self.assertEqual(n2.successor, d0)
        self.assertEqual(n2.predecessor, d1)

    def test_get_neighbors(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)
        d2 = node_ranked(2);    n2 = ncore.NodeCore(d2)

        reactor = NodeReactor(n0, n1, n2)

        msg = ncore.GetNeighbors(destination = d1)
        result = n1.handle_message(msg)

        self.assertDeepEqual(result,
                ncore.NodeList(nodes=[d0,d2]))

    def test_leader_new_node_own_leader(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        self.assertEqual(n0.leader, d0)

    def test_leader_assigned_on_join(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)

        reactor = NodeReactor(n0)
        reactor.join_node(n1)

        # Original leader should remain unchanged (Ring structure is about minimal disruption)
        self.assertEqual(n0.leader, d0)

        # New node should take original leader (again, minimal disruption)
        self.assertEqual(n1.leader, d0)

    def test_get_leader(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)

        reactor = NodeReactor(n0, n1)

        msg = ncore.GetLeader(destination = d0)
        result = n1.handle_message(msg)

        self.assertEqual(result,
                ncore.NodeList(nodes=[d0]))

    def test_election_single_node(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)

        msg = ncore.Election(destination = d0, participants=[])
        result = n0.handle_message(msg)

        self.assertEqual(result, ncore.GenericOk())
        self.assertEqual(n0.leader, d0)

    def test_election_fwd(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)
        reactor = NodeReactor(n0, n1)

        msg = ncore.Election(destination = d0, participants=[])
        result = n0.handle_message(msg)

        # It should add its name to the list and forward to the next node
        self.assertDeepEqual(result,
                ncore.GenericOk(new_messages=[
                        ncore.Election(destination=d1, participants=[d0])
                    ]))

    def test_election_win(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)
        reactor = NodeReactor(n0, n1)

        msg = ncore.Election(destination = d0, participants=[d0,d1])
        result = n0.handle_message(msg)

        # It should declare itself the winner
        self.assertDeepEqual(result,
                ncore.GenericOk(new_messages=[
                        ncore.ElectionResult(destination=d1, new_leader=d0)
                    ]))

    def test_election_result_fwd(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)
        reactor = NodeReactor(n0, n1)

        msg = ncore.ElectionResult(destination=d0, new_leader=d1)
        result = n0.handle_message(msg)

        # It should set its leader and forward the message
        self.assertEqual(n0.leader, d1)
        self.assertDeepEqual(result,
                ncore.GenericOk(new_messages=[
                        ncore.ElectionResult(destination=d1, new_leader=d1)
                    ]))

    def test_election_result_finish(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)
        reactor = NodeReactor(n0, n1)

        msg = ncore.ElectionResult(destination=d1, new_leader=d1)
        result = n1.handle_message(msg)

        # It should set its leader and forward the message
        self.assertEqual(n1.leader, d1)
        self.assertDeepEqual(result, ncore.GenericOk())

    def test_election_together(self):
        d0 = node_ranked(0);    n0 = ncore.NodeCore(d0)
        d1 = node_ranked(1);    n1 = ncore.NodeCore(d1)
        d2 = node_ranked(2);    n2 = ncore.NodeCore(d2)

        reactor = NodeReactor(n0, n1, n2)

        msg = ncore.Election(destination=d2)
        reactor.send_msg(msg)
        self.assertEqual(n0.leader, d2)
        self.assertEqual(n1.leader, d2)
        self.assertEqual(n2.leader, d2)

        msg = ncore.Election(destination=d1)
        reactor.send_msg(msg)
        self.assertEqual(n0.leader, d1)
        self.assertEqual(n1.leader, d1)
        self.assertEqual(n2.leader, d1)



class NodeReactor:
    """ Simulated network of nodes that automatically propagates messages

    For easier test setup
    """

    def __init__(self, *nodes):
        self.nodes = dict()
        for node in nodes:
            self.join_node(node)

    def join_node(self, new_node):
        """ Add a node to the reactor, and have it join the simulated network """
        if len(self.nodes) > 0:
            existing = self.nodes.itervalues().next()
        else:
            existing = None

        self.nodes[new_node.descriptor.host_port] = new_node

        if existing:
            self.send_msg(
                    ncore.Join(
                        destination=existing.descriptor,
                        new_node=new_node.descriptor))

    def send_msg(self, msg):
        """ Send a message, and propagate any new messages from the result """
        # print("delivering", msg)
        target = self.nodes[msg.destination.host_port]
        result = target.handle_message(msg)
        for newmsg in result.new_messages:
            self.send_msg(newmsg)
        return result

if __name__ == '__main__':
    unittest.main()
