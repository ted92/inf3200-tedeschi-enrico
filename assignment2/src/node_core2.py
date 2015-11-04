#!/usr/bin/env python
# coding=utf-8

import hashlib
import collections
import logging

loghandler = logging.StreamHandler()
loghandler.setFormatter(logging.Formatter(
    '%(msecs)03.4f %(name)-12s %(levelname)-8s -- %(core)s - %(message)s'))

logger = logging.getLogger("node_core")
logger.setLevel(logging.INFO)
logger.addHandler(loghandler)

def node_hash(s):
    """ Map input to the node key space """
    md5 = hashlib.md5()
    md5.update(s)
    hexhash = md5.hexdigest()
    numerichash = long(hexhash,16)
    return numerichash


class NodeDescriptor:
    """ Essential node metadata for addressing and ranking a node """

    def __init__(self, host=None, port=None, host_port=None):
        if host!=None and port!=None:
            (self.host, self.port) = (host.strip(), port)
        elif host_port!=None:
            (self.host, self.port) = host_port.strip().split(":")
        else:
            raise RuntimeError( "Bad %s: host='%s', port='%s', host_port='%s'"
                % (self.__class__.__name__, host, port, host_port) )

        self.port = int(self.port)
        self.host_port = "%s:%s" % (self.host, self.port)
        self.rank = node_hash(self.host_port)

    def __repr__(self):
        return ("<%s,%s‥>"
            % (self.host_port, str(self.rank)[0:6]))

    def __str__(self):
        return "%s:%s" % (self.host, self.port)

    def __eq__(a, b):
        return isinstance(b,NodeDescriptor) and a.__dict__ == b.__dict__


# Node Messages
# All messages should have a 'destination' field

Join = collections.namedtuple("Join",
        ["destination", "new_node"])


JoinAccepted = collections.namedtuple("JoinAccepted",
        ['destination', 'successor', 'predecessor', 'leader'])
JoinAccepted.__new__.__defaults__ = (None, None, None, None)


NewPredecessor = collections.namedtuple("NewPredecessor",
        ["destination", "predecessor"])

Election = collections.namedtuple("Election",
        ["destination", "participants"])
Election.__new__.__defaults__ = (None, [])

ElectionResult = collections.namedtuple("ElectionResult",
        ["destination", "new_leader"])

GetNeighbors = collections.namedtuple("GetNeighbors",
        ["destination"])

GetLeader = collections.namedtuple("GetLeader",
        ["destination"])


# Direct Node Responses
# All direct responses should have a 'new_messages' field

# An OK message with no content
GenericOk = collections.namedtuple("GenericOk",
        ["new_messages"])
GenericOk.__new__.__defaults__ = ([],)

# A simple list of node descriptors.
# Semantics depends on the call.
#   GetNeighbors will return a list of neighbors.
#   GetLeader will return a list with one element: the leader.
NodeList = collections.namedtuple("NodeList",
        ["new_messages", "nodes"])
NodeList.__new__.__defaults__ = ([],[])


# Core Logic of Node

class NodeCore:
    def __init__(self, descriptor):

        self.descriptor = descriptor        # This node's descriptor
        self.successor = None               # Successor node's descriptor

        # Remembering predecessor is necessary for graceful shutdown.
        self.predecessor = None             # Predecessor node's descriptor

        # If a node is in a network by itself, it is the leader.
        self.leader = descriptor

        self.logger = logging.LoggerAdapter(logger, {'core':self.descriptor})

        self.logger.debug("New node core created")

    def responsible_for_key(self, key):
        """ Hashes the key and decides if the hash is in range to be handled by this node """
        key_hash = node_hash(key)
        return self.responsible_for_hash(key_hash)


    def responsible_for_hash(self, key_hash):
        """ Decides if the hash is in range to be handled by this node """

        d = self.descriptor
        s = self.successor

        if (s == None):
            # Single node
            return True
        elif (d.rank < s.rank):
            # Normal
            return d.rank <= key_hash and key_hash < s.rank
        else:
            # Wrap-around
            return d.rank <= key_hash or key_hash < s.rank


    def handle_message(self, msg):
        """ Handle a message

        Returns either a direct response object,
        or a list of new messages to send.
        """

        if isinstance(msg, Join):

            d = self.descriptor
            n = msg.new_node
            s = self.successor

            if self.responsible_for_hash(n.rank):

                ns = s if s else d
                self.successor = n

                newmsgs = []

                if self.predecessor==None:
                    self.logger.debug("Join(%s): accepting", n)
                    self.predecessor = n
                else:
                    self.logger.debug("Join(%s): accepting and notifying %s", n,s)
                    newmsgs.append(
                            NewPredecessor( destination=s, predecessor=n ) )

                newmsgs.append(
                        JoinAccepted(
                            destination=n,
                            successor=ns, predecessor=d,
                            leader=self.leader) )

                return GenericOk(newmsgs)

            else:
                self.logger.debug("Join(%s): forwarding to %s", n,s)
                return GenericOk([ msg._replace(destination=s) ])

        elif isinstance(msg, JoinAccepted):
            self.logger.debug("JoinAccepted: New successor=%s, predecessor=%s", msg.successor, msg.predecessor)
            self.successor = msg.successor
            self.predecessor = msg.predecessor
            self.leader = msg.leader
            return GenericOk()

        elif isinstance(msg, NewPredecessor):
            self.logger.debug("NewPredecessor: %s", msg.predecessor)
            self.predecessor = msg.predecessor
            return GenericOk()

        elif isinstance(msg, Election):
            if self.successor == None:
                # Single node. You are already the leader. No one else to elect.
                self.logger.debug("Election: Single node. I am already my own leader.")
                return GenericOk()
            if self.descriptor in msg.participants:
                # Message has re-reached you. You win.
                self.logger.debug("Election: Message returned to me. I am winner.")
                announce = ElectionResult(
                        destination = self.successor,
                        new_leader = self.descriptor
                        )
                return GenericOk(new_messages=[announce])
            else:
                # You are the next participant, add your name and forward.
                self.logger.debug("Election: forwarding to %s", self.successor)
                fwd = Election(
                        destination = self.successor,
                        participants = msg.participants + [self.descriptor]
                        )
                return GenericOk(new_messages=[fwd])

        elif isinstance(msg, ElectionResult):
            self.leader = msg.new_leader
            if msg.new_leader == self.descriptor:
                self.logger.debug("ElectionResult(%s): message has completed round. I am confirmed leader.", msg.new_leader)
                # Message has completed it's trip around the ring.
                # You are confirmed as the winner.
                return GenericOk()
            else:
                self.logger.debug("ElectionResult(%s): forwarding to %s", msg.new_leader, self.successor)
                return GenericOk(new_messages = [
                    msg._replace(destination = self.successor)
                    ])

        elif isinstance(msg, GetNeighbors):
            neighbors = []
            if self.predecessor: neighbors.append(self.predecessor)
            if self.successor: neighbors.append(self.successor)
            return NodeList(nodes=neighbors)

        elif isinstance(msg, GetLeader):
            return NodeList(nodes=[self.leader])

        else:
            raise RuntimeError("Unknown message: %s" % (msg,))
