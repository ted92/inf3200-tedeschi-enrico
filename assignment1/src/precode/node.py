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
from pprint import pprint
from pprint import pformat

import node_request

MAX_CONTENT_LENGHT = 1024		# Maximum length of the content of the http request (1 kilobyte)
MAX_STORAGE_SIZE = 104857600	# Maximum total storage allowed (100 megabytes)

node_httpserver_port = 8000

# Concise way to get MD5 of a string
def md5_string(s):
    md5 = hashlib.md5()
    md5.update(s)
    digest = md5.hexdigest()
    return digest

# Hashing function to map string keys to integer key space
def node_hash(s):
    hexhash = md5_string(s)
    numerichash = long(hexhash,16)
    return numerichash


# Classes that represent response actions

class ValueFound:
    def __init__(self, value):
        self.value = value

class ValueNotFound: pass

class ValueStored: pass

class ForwardRequest:
    def __init__(self, destination):
        self.destination = destination


class Node:

    def __init__(self, num_hosts, rank, next_node):
        self.map = dict()
        self.size = 0
        self.num_hosts = long(num_hosts)
        self.rank = long(rank)
        self.next_node = next_node
        pprint(self.__dict__, indent=2)

    def responsible_for_key(self, key):
        key_hash = node_hash(key)
        return self.rank == key_hash % self.num_hosts

    def do_put(self, key, value):
        if self.responsible_for_key(key):
            self.map[key] = value
            return ValueStored()
        else:
            return ForwardRequest(self.next_node)

    def do_get(self, key):
        if self.responsible_for_key(key):
            value = self.map.get(key)
            if value: return ValueFound(value)
            else: return ValueNotFound()
        else:
            return ForwardRequest(self.next_node)

    def get_value(self, key):
        return self.map.get(key)

    def put_value(self, key, value, size):
        self.size = self.size + size
        self.map[key] = value

    def get_num_hosts(self):
        return self.num_hosts

    def get_rank(self):
        return self.rank

    def get_next_node(self):
        return self.next_node



class NodeHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    global node

    # Insert the key
    def do_GET(self):
        key = self.path

        result = node.do_get(key)

        if isinstance(result, ValueFound):
            self.respond(200, "application/octet-stream", result.value)

        elif isinstance(result, ValueNotFound):
            self.respond(404, "text/html", "Key not found")

        elif isinstance(result, ForwardRequest):
            node_request.sendGET(result.destination, node_httpserver_port, key)

        else:
            raise Exception("Unknown result command: " + pformat(result))


    def do_PUT(self):
        key = self.path

        contentLength = int(self.headers['Content-Length'])

        if contentLength <= 0 or contentLength > MAX_CONTENT_LENGHT:
            self.respond(400, "text/html", "Content body too large")
            return

        value = self.rfile.read(contentLength)

        result = node.do_put(key, value)

        if isinstance(result, ValueStored):
            self.respond(200, "application/octet-stream", "")

        elif isinstance(result, ForwardRequest):
            node_request.sendPUT(result.destination, node_httpserver_port, key, value)

        else:
            raise Exception("Unknown result command: " + pformat(result))


    def respond(self, status_code, content_type, body):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(body)


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
    node = Node(sys.argv[1], sys.argv[2], sys.argv[3])

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
