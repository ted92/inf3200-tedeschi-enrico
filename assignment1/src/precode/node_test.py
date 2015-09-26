#!/usr/bin/python
# vim: set sts=4 sw=4 et:

import unittest
import node

class TestNode(unittest.TestCase):

    def test_process(self):
        nodeObj = node.Node()
        self.assertTrue(isinstance(nodeObj, node.Node))

class TestNodeServer(unittest.TestCase):

    def test_server_startup(self):
        server = node.NodeServer()
        self.assertTrue(isinstance(server, node.NodeServer))

if __name__ == '__main__':
    unittest.main()
