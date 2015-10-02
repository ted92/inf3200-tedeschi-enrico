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

# Convenience method to concisely hash a string with MD5
def md5_string(s):
    md5 = hashlib.md5()
    md5.update(s)
    digest = md5.hexdigest()
    return digest

# Hashing function to map string keys to an integer key space
def node_hash(s):
    hexhash = md5_string(s)
    numerichash = long(hexhash,16)
    return numerichash


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
class NodeCore:

    def __init__(self, num_hosts, rank, next_node):
        self.map = dict()
        self.size = 0
        self.num_hosts = long(num_hosts)
        self.rank = long(rank)
        self.next_node = next_node

    # Hashes the key into the key space and decides if this key is in range to
    # be handled by this node.
    def responsible_for_key(self, key):
        # First hash the key using a standard hashing algorithm.
        # Then do a modulo operation on the number of nodes in the cluster.
        # This effectively maps the key to a key space of integers from 0 to n-1.
        # Each node is responsible for one integer in this key space.
        key_hash = node_hash(key)
        rank_responsible = key_hash % self.num_hosts
        return rank_responsible == self.rank


    # Handle a request to store a key-value pair
    #
    # Returns a ValueStored instance if the value was stored successfully, or a
    # ForwardReqest instance if the request should be forwarded to another node.
    #
    def do_put(self, key, value):
        if self.responsible_for_key(key):
            self.map[key] = value
            # TODO: update size. Use size for something?
            return ValueStored()
        else:
            return ForwardRequest(self.next_node)

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
            return ForwardRequest(self.next_node)



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
            value = node_request.sendGET(result.destination, node_httpserver_port, key)
            # Interpret response and send response
            # TODO: just mimic response
            if value:
                self.respond(200, "application/octet-stream", value)
            else:
                self.respond(404, "text/html", "Key not found")

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
            node_request.sendPUT(result.destination, node_httpserver_port, key, value)
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

    # sys.argv[1] --> num_hosts
    # sys.argv[2] --> rank
    # sys.argv[3] --> next_node
    node = NodeCore(sys.argv[1], sys.argv[2], sys.argv[3])

    # Start the webserver which handles incomming requests
    # TODO: accept parameters from command line:
    #   total number of nodes, rank of this node, name of next node
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
