#!/usr/bin/env python

import BaseHTTPServer
import argparse
import collections
import httplib
import signal
import threading

import node_core2 as ncore

# Verbose output trace

verbose = False

def verbosep(msg):
    """ Print string if verbose output is on """
    if verbose:
        if server_node_core:
            print("%s: %s" % (server_node_core.descriptor.host_port, msg))
        else:
            print(strs)


# HTTP Abstractions

class HttpRequest:
    """ Abstraction of an HTTP request to a node """
    def __init__(self,
            host=None, port=80,
            destination=None,
            method="POST", path="", body=""):

        if host!=None:
            self.host = host
            self.port = port
            self.destination = ncore.NodeDescriptor(host=host, port=port)

        if isinstance(destination, ncore.NodeDescriptor):
            self.destination = destination
            self.host = destination.host
            self.port = destination.port

        self.method = method
        self.path = path
        self.body = body


# Convert HTTP to and from Node Messages

def parse_single_node_descriptor(s):
    """ Parse a string as a single node descriptor host:port """
    return ncore.NodeDescriptor(host_port = s.strip())

def parse_node_descriptor_dict(s):
    """ Parse a string as a list of roles and descriptors

    For example:

        successor=localhost:8002
        predecessor=localhost:8001
    """
    rdmap = dict()
    lines = s.split("\n")
    for line in lines:
        if line.strip() == "": continue
        (role, hp) = line.split("=")
        rdmap[role.strip()] = ncore.NodeDescriptor(host_port=hp.strip())
    return rdmap


def build_request(msg):
    """ Build an HttpRequest for a node message """

    if isinstance(msg, ncore.Join):
        return HttpRequest(
                destination = msg.destination,
                method = "POST",
                path = "join",
                body = msg.new_node.host_port)

    if isinstance(msg, ncore.JoinAccepted):
        return HttpRequest(
                destination = msg.destination,
                method = "POST",
                path = "join/accepted",
                body =
"""successor = %s
predecessor = %s
""" % (msg.successor, msg.predecessor) )

    if isinstance(msg, ncore.NewPredecessor):
        return HttpRequest(
                destination = msg.destination,
                method = "PUT",
                path = "predecessor",
                body = msg.predecessor.host_port)

    else:
        raise RuntimeError("Do not know how to build HTTP for message %s" % (msg,))


def parse_request(hr):
    """ Parse an HttpRequest to one of the node message types """

    if hr.path=="join" and hr.method=="POST":
        new_node = parse_single_node_descriptor(hr.body)
        return ncore.Join(destination=hr.destination, new_node=new_node)

    if hr.path=="join/accepted" and hr.method=="POST":
        rolemap = parse_node_descriptor_dict(hr.body)
        return ncore.JoinAccepted(
                destination=hr.destination,
                successor=rolemap["successor"],
                predecessor=rolemap["predecessor"] )

    if hr.path=="predecessor" and hr.method=="PUT":
        p = parse_single_node_descriptor(hr.body)
        return ncore.NewPredecessor(destination=hr.destination, predecessor=p)

    else:
        raise RuntimeError("Do not know how to parse request %s %s" % (hr.method, hr.path))



# Actually Send Requests

def send_message(msg):
    """ Send a message to another node """
    verbosep("Sending message: %s" % (msg,))
    hr = build_request(msg)
    send_request(hr)


def send_request(hr):
    """ Actually send a request to a server via HTTP """

    conn = httplib.HTTPConnection(hr.host, hr.port)
    conn.request(hr.method, hr.path, hr.body)
    verbosep("Sent request: %s:%d %s %s '%s'" %
            (hr.host, hr.port, hr.method, hr.path, hr.body))

    # Must read response even if we don't do anything with it.
    # If we don't, the server will get broken pipe errors.
    #	1. Return without reading response
    #	2. Server might not be finish sending response yet.
    #	3. Library code here closes connection.
    #	4. Server code tries to finish writing to closed pipe.
    #	5. Broken pipe.
    response = conn.getresponse()
    data = response.read()

    if response.status!=200:
        raise

    verbosep("Request OK: %s %s" % (hr.method, hr.path))


# Actually Run as a Server

server_node_core = None     # Core decision module for server

class HttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    global server_node_core

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def handle_request(self, method):
        verbosep("Receiving request: %s %s" % (method, self.path))
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        msg = parse_request(HttpRequest(
                destination = server_node_core.descriptor,
                method = method,
                path = self.path,
                body = body))

        verbosep("Parsed message: %s" % (msg,))
        action = server_node_core.handle_message(msg)

        self.respond_ok()
        for newmsg in action:
            send_message(newmsg)

    def respond_ok(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("")



# ----------------------------------------------------------
# Basic HTTP server
#
class NodeServer(BaseHTTPServer.HTTPServer):

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

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true",
            help="debug trace")
    parser.add_argument("host_port", metavar="host:port",
            help="external hostname (or IP) and port for this server")
    parser.add_argument("--join", metavar="host:port", default=None,
            help="another server to join")
    args = parser.parse_args()

    verbose = args.verbose
    descriptor = ncore.NodeDescriptor(host_port=args.host_port)
    join_descriptor = ncore.NodeDescriptor(host_port=args.join) if args.join else None
    server_node_core = ncore.NodeCore(descriptor)

    # Start the webserver which handles incomming requests
    verbosep("Starting HTTP server: %s, %s" % (descriptor, descriptor.rank))
    httpd = NodeServer((descriptor.host, descriptor.port), HttpRequestHandler)
    server_thread = threading.Thread(target = httpd.serve)
    server_thread.daemon = True
    server_thread.start()

    def handler(signum, frame):
        verbosep("Stopping http server...")
        httpd.stop()
    signal.signal(signal.SIGINT, handler)

    # Join network
    if join_descriptor:
        joinmsg = ncore.Join(destination=join_descriptor, new_node=descriptor)
        send_message(joinmsg)

    # Wait for server thread to exit
    server_thread.join(100)
