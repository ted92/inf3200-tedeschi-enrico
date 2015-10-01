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
import httplib

MAX_CONTENT_LENGHT = 1024		# Maximum length of the content of the http request (1 kilobyte)
MAX_STORAGE_SIZE = 104857600	# Maximum total storage allowed (100 megabytes)

node_httpserver_port = 8000

class Node:

    def __init__(self, num_hosts, rank, next_node):
        self.map = dict()
        self.size = 0
        self.num_hosts = long(num_hosts)
        self.rank = long(rank)
        self.next_node = next_node

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

    # to PUT an hash value in the next node
    def sendPUT(self, key, value):
		node = self.next_node;
		conn = httplib.HTTPConnection(node, node_httpserver_port)
		conn.request("PUT", "/%s" % key, value)

    # to GET an hash value from the next node
    def sendGET(self, key):
		node = self.next_node
		conn = httplib.HTTPConnection(node, node_httpserver_port)
		conn.request("GET", "/%s" % key)
		response = conn.getresponse()
		data = response.read()

		return data

class NodeHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    global node
    # sys.argv[1] --> num_hosts
    # sys.argv[2] --> rank
    # sys.argv[3] --> next_node
    node = Node(sys.argv[1], sys.argv[2], sys.argv[3])

    # Insert the key
    def do_GET(self):
        key = self.path

        key_md5 = self.get_md5(key)

        # if is the right node then check if the key exists
        if(node.rank == key_md5 % node.num_hosts):
            value = node.get_value(key)

            #if the key doesn't exist then return 404
            if value is None:
                self.sendErrorResponse(404, "Key not found")
                return

            # Write header
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.end_headers()


            # Write Body
            self.wfile.write(value)

        else:
            # forward the get request to the next node
            node.sendGET(self.path)

    def do_PUT(self):
        key = self.path

        # convert the key with md5 value
        key_md5 = self.get_md5(key)

        contentLength = int(self.headers['Content-Length'])

        if contentLength <= 0 or contentLength > MAX_CONTENT_LENGHT:
            self.sendErrorResponse(400, "Content body to large")
            return

        # put the value only if the key value is right according to 'rank == md5(key) % num_hosts'
        if (node.rank == key_md5 % node.num_hosts):
            # if is the right node, then save the data in the map
            node.put_value(key, self.rfile.read(contentLength), contentLength)
            # print "value saved in rank: ", node.rank, " with md5(key) value: ", (key_md5 % node.num_hosts)
            self.send_response(200)
            # self.send_header("Content-type", "text/html")
            # self.end_headers()
        else:
            # otherwise call the next node
            node.sendPUT(self.path, self.rfile.read(contentLength))

    def sendErrorResponse(self, code, msg):
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(msg)

    # method to get the md5 of a key
    def get_md5(self, key):
        md5 = hashlib.md5()
        md5.update(key)
        digest = md5.hexdigest()
        md5_key = int(digest, 16)

        return md5_key

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
