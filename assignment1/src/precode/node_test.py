#!/usr/bin/python
# vim: set sts=4 sw=4 et:

import unittest
import node

class TestNode(unittest.TestCase):

    def test_put_value_get_value(self):
        nodeObj = node.Node()
        key = "hello_world"
        value = "Hello world!"
        nodeObj.put_value(key, value, len(value))
        retrieved = nodeObj.get_value(key)
        self.assertEqual(retrieved, value)

    def test_size(self):
        nodeObj = node.Node()
        key = "hello_world"
        value = "Hello world!"
        nodeObj.put_value(key, value, len(value))
        self.assertEqual(nodeObj.size, len(value))


if __name__ == '__main__':
    unittest.main()
