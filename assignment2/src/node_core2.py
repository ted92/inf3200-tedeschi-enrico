#!/usr/bin/env python

import hashlib
import collections

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
            (self.host, self.port) = (host, port)
        elif host_port!=None:
            (self.host, self.port) = host_port.split(":")
        else:
            raise RuntimeError( "Bad %s: host='%s', port='%s', host_port='%s'"
                % (self.__class__.__name__, host, port, host_port) )

        self.host_port = "%s:%s" % (self.host, self.port)
        self.rank = node_hash(self.host_port)

    def __repr__(self):
        return ("<%s.%s %s,%s>"
            % (self.__class__.__module__, self.__class__.__name__,
                self.host_port, self.rank))

    def __str__(self):
        return "%s:%s" % (self.host, self.port)


# Node Messages

Join = collections.namedtuple("Join", ["destination", "new_node"])
JoinAccepted = collections.namedtuple("JoinAccepted", ['destination', 'successor'])


# Direct Node Responses

GenericOk = collections.namedtuple("GenericOk", [])


# Core Logic of Node

class NodeCore:
    def __init__(self, descriptor):
        self.descriptor = descriptor        # This node's descriptor
        self.successor = None               # Successor node's descriptor


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


    def handle_message(self, ar):
        """ Handle a message

        Returns either a direct response object,
        or a list of new messages to send.
        """

        d = self.descriptor
        s = self.successor

        if isinstance(ar, Join):

            n = ar.new_node

            if self.responsible_for_hash(n.rank):

                ns = s if s else d
                self.successor = n
                return [ JoinAccepted(destination=n, successor=ns) ]

            else:
                ar.destination = s
                return [ ar ]

        if isinstance(ar, JoinAccepted):
            self.successor = ar.successor
            return GenericOk()
