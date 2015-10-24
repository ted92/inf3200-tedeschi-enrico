#!/usr/bin/python
# vim: set sts=4 sw=4 et:

import BaseHTTPServer
import SocketServer
import time
import threading
import signal
import sys
import os
import getopt
import hashlib
from pprint import pformat

import node_request

MAX_CONTENT_LENGHT = 1024		# Maximum length of the content of the http request (1 kilobyte)
MAX_STORAGE_SIZE = 104857600	# Maximum total storage allowed (100 megabytes)

node_httpserver_port = 8000

# Hashing function to map string keys to an integer key space
def node_hash(s):
    md5 = hashlib.md5()
    md5.update(s)
    hexhash = md5.hexdigest()
    numerichash = long(hexhash,16)
    return numerichash



class NodeDescriptor:
    """ Essential data about a node (IP, port) that is hashed to obtain its rank """

    def __init__(self, ip=None, port=None, ip_port=None):
        if ip!=None and port!=None:
            (self.ip, self.port) = (ip, port)
        elif ip_port!=None:
            (self.ip, self.port) = ip_port.split(":")
        else:
            raise RuntimeError( "Bad NodeDescriptor: ip='%s', port='%s', ip_port='%s'" % (ip, port, ip_port) )

        self.ip_port = "%s:%s" % (self.ip, self.port)
        self.rank = node_hash(self.ip_port)

    def __repr__(self):
        return "%s.%s (%s:%s, %s)" % (self.__class__.__module__, self.__class__.__name__, self.ip, self.port, self.rank)

    def __str__(self):
        return "%s:%s" % (self.ip, self.port)


# ----------------------------------------------------------
# Small classes that represent node search results
#

class ValueFound:
    def __init__(self, value):
        self.value = value

class ValueNotFound: pass

class ValueStored: pass

class ForwardRequest:
    def __init__(self, destination):
        self.destination = destination


# ----------------------------------------------------------
# Core logic of a node.
#
# Separated from HTTP handling for easier testing.
#
# On this level, node IDs are node rank, and they are numeric values found by
# hashing the relevant data (IP:port,etc) on the server level.
#
class NodeCore:

    def __init__(self, *args, **kwargs):
        # desc=None, predecessor=None, succesor=None):
        self.map = dict()

        if "desc" in kwargs:
            desc = kwargs['desc']
            predecessor = kwargs["predecessor"] if "predecessor" in kwargs else None
            successor = kwargs["successor"] if "successor" in kwargs else None

            self.desc = desc
            self.predecessor = predecessor
            self.successor = successor
        else:
            node_count = long(args[0])
            rank = long(args[1])
            next_node = args[2]

            self.node_count = node_count
            self.rank = rank
            self.next_node = next_node

            long_max_digit = 100000000000000000000000000000000000000L

            self.desc = NodeDescriptor(ip="127.0.0.1", port=node_httpserver_port)
            self.desc.rank = rank * long_max_digit

            if rank+1 >= node_count:
                next_rank = 0
            else:
                next_rank = rank+1

            self.successor = NodeDescriptor(ip=next_node, port=node_httpserver_port)
            self.successor.rank = next_rank * long_max_digit

    def responsible_for_key(self, key):
        """ Hashes the key and decides if the hash is in range to be handled by this node """
        key_hash = node_hash(key)
        if (self.successor == None):
            # Single node
            return True
        elif (self.desc.rank < self.successor.rank):
            # Normal
            return self.desc.rank <= key_hash and key_hash < self.successor.rank
        else:
            # Wrap-around
            return self.desc.rank <= key_hash or key_hash < self.successor.rank


    # Handle a request to store a key-value pair
    #
    # Returns a ValueStored instance if the value was stored successfully, or a
    # ForwardReqest instance if the request should be forwarded to another node.
    #
    def do_put(self, key, value):
        if self.responsible_for_key(key):
            self.map[key] = value
            return ValueStored()
        else:
            return ForwardRequest(self.successor)

    # Handle a request to look up a key
    #
    # Returns a ValueFound instance if the value was found in this node, a
    # ValueNotFound instance if this node is responsible for the key but there
    # is nothing stored there yet, and a ForwardReqest instance if the request
    # should be forwarded to another node.
    #
    def do_get(self, key):
        if self.responsible_for_key(key):
            value = self.map.get(key)
            if value: return ValueFound(value)
            else: return ValueNotFound()
        else:
            return ForwardRequest(self.successor)



# ----------------------------------------------------------
# HTTP interpreting logic of a node
#
# Handles HTTP requests and sends responses, but defers to NodeCore for actual
# decisionmaking.
#
class NodeHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    global node

    # Handle a GET request, to look up a key
    def do_GET(self):
        # The URL path is the key
        key = self.path

        # Defer to NodeCore
        result = node.do_get(key)

        # Take action depending on NodeCore decision
        if isinstance(result, ValueFound):
            self.respond(200, "application/octet-stream", result.value)

        elif isinstance(result, ValueNotFound):
            self.respond(404, "text/html", "Key not found")

        elif isinstance(result, ForwardRequest):
            # Forward request to specified node
            (status_code, content_type, data) = node_request.sendGET(
                    result.destination.ip, result.destination.port, key)

            # Relay response to requesting node
            self.respond(status_code, content_type, data)

        else:
            raise Exception("Unknown result command: " + pformat(result))


    # Handle a PUT request, to store a key-value pair
    def do_PUT(self):
        # The URL path is the key
        key = self.path

        # Reject values that are too long
        contentLength = int(self.headers['Content-Length'])

        if contentLength <= 0 or contentLength > MAX_CONTENT_LENGHT:
            self.respond(400, "text/html", "Content body too large")
            return

        # The value is the body of the PUT request
        value = self.rfile.read(contentLength)

        # Defer to NodeCore
        result = node.do_put(key, value)

        # Take action depending on NodeCore decision
        if isinstance(result, ValueStored):
            self.respond(200, "application/octet-stream", "")

        elif isinstance(result, ForwardRequest):
            node_request.sendPUT(result.destination.ip, result.destination.port, key, value)
            self.respond(200, "application/octet-stream", "")

        else:
            raise Exception("Unknown result command: " + pformat(result))


    # Convenience method to make it easier to send responses
    def respond(self, status_code, content_type, body):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(body)


# ----------------------------------------------------------
# Basic HTTP server
#
class NodeServer(BaseHTTPServer.HTTPServer, SocketServer.ForkingMixIn, SocketServer.ThreadingMixIn):

    def server_bind(self):
        BaseHTTPServer.HTTPServer.server_bind(self)
        self.socket.settimeout(1)
        self.run = True

    def get_request(self):
        while self.run == True:
            try:
                sock, addr = self.socket.accept()
                sock.settimeout(None)
                return (sock, addr)
            except socket.timeout:
                if not self.run:
                    raise socket.error

    def stop(self):
        self.run = False

    def serve(self):
        while self.run == True:
            self.handle_request()


if __name__ == '__main__':

    httpserver_port = 8000

    # sys.argv[1] --> node_count
    # sys.argv[2] --> rank
    # sys.argv[3] --> next_node
    node_count = sys.argv[1]
    rank = long(sys.argv[2])
    next_node = sys.argv[3]
    node = NodeCore(node_count, rank, next_node)

    # Start the webserver which handles incomming requests
    try:
        print "Starting HTTP server on port %d" % httpserver_port
        httpd = NodeServer(("",httpserver_port), NodeHttpHandler)
        server_thread = threading.Thread(target = httpd.serve)
        server_thread.daemon = True
        server_thread.start()

        def handler(signum, frame):
            print "Stopping http server..."
            httpd.stop()
        signal.signal(signal.SIGINT, handler)

    except Exception as e:
        print "Error: unable to start http server thread"
        raise e

    # Wait for server thread to exit
    server_thread.join(100)
