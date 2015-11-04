#!/usr/bin/env python

import BaseHTTPServer
import Queue
import argparse
import collections
import httplib
import logging
import signal
import threading

import node_core2 as ncore

# Logging Setup

loghandler = logging.StreamHandler()
loghandler.setFormatter(logging.Formatter(
    '%(msecs)03.4f %(name)-12s %(levelname)-8s -- %(core)s - %(message)s'))

logger = logging.getLogger("node_http")
logger.setLevel(logging.INFO)
logger.addHandler(loghandler)

class CoreFilter(logging.Filter):
    def filter(self, record):
        if (server_node_core):
            record.core = server_node_core.descriptor
        else:
            record.core = "no core"
        return True

logger.addFilter(CoreFilter())


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

        if not path.startswith("/"):
            path = "/" + path
        self.path = path

        self.body = body


class HttpResponse:
    """ Abstraction of an HTTP response to a node request """
    def __init__(self, status=200, body=""):
        self.status = status
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

def build_node_descriptor_list(node_list):
    """ Produce a simple list of host:port pairs, one on each line. """
    return "\n".join( [n.host_port for n in node_list] )

def parse_node_descriptor_list(s):
    s = s.strip()
    if s=='':
        return []
    else:
        return [ncore.NodeDescriptor(host_port=hp) for hp in s.split("\n")]


def build_request(msg):
    """ Build an HttpRequest for a node message """

    if isinstance(msg, ncore.Join):
        return HttpRequest(
                destination = msg.destination,
                method = "POST",
                path = "/join",
                body = msg.new_node.host_port)

    if isinstance(msg, ncore.JoinAccepted):
        return HttpRequest(
                destination = msg.destination,
                method = "POST",
                path = "/join/accepted",
                body =
"""successor = %s
predecessor = %s
leader = %s
""" % (msg.successor, msg.predecessor, msg.leader) )

    if isinstance(msg, ncore.NewPredecessor):
        return HttpRequest(
                destination = msg.destination,
                method = "PUT",
                path = "/predecessor",
                body = msg.predecessor.host_port)

    if isinstance(msg, ncore.Election):
        return HttpRequest(
                destination = msg.destination,
                method = "POST",
                path = "/election",
                body = build_node_descriptor_list(msg.participants))

    if isinstance(msg, ncore.ElectionResult):
        return HttpRequest(
                destination = msg.destination,
                method = "POST",
                path = "/election/result",
                body = msg.new_leader.host_port)

    if isinstance(msg, ncore.GetNeighbors):
        return HttpRequest(
                destination = msg.destination,
                method = "GET",
                path = "/getNodes")

    if isinstance(msg, ncore.GetLeader):
        return HttpRequest(
                destination = msg.destination,
                method = "GET",
                path = "/getCurrentLeader")
    else:
        raise RuntimeError("Do not know how to build HTTP for message %s" % (msg,))


def parse_request(hr):
    """ Parse an HttpRequest to one of the node message types """

    if hr.path=="/join" and hr.method=="POST":
        new_node = parse_single_node_descriptor(hr.body)
        return ncore.Join(destination=hr.destination, new_node=new_node)

    if hr.path=="/join/accepted" and hr.method=="POST":
        rolemap = parse_node_descriptor_dict(hr.body)
        return ncore.JoinAccepted(
                destination=hr.destination,
                successor=rolemap["successor"],
                predecessor=rolemap["predecessor"],
                leader=rolemap["leader"])

    if hr.path=="/predecessor" and hr.method=="PUT":
        p = parse_single_node_descriptor(hr.body)
        return ncore.NewPredecessor(destination=hr.destination, predecessor=p)

    if hr.path=="/election" and hr.method=="POST":
        p = parse_node_descriptor_list(hr.body)
        return ncore.Election(destination=hr.destination, participants=p)

    if hr.path=="/election/result" and hr.method=="POST":
        nl = parse_single_node_descriptor(hr.body)
        return ncore.ElectionResult(destination=hr.destination, new_leader=nl)

    if hr.path=="/getNodes" and hr.method=="GET":
        return ncore.GetNeighbors(destination=hr.destination)

    if hr.path=="/getCurrentLeader" and hr.method=="GET":
        return ncore.GetLeader(destination=hr.destination)

    else:
        raise RuntimeError("Do not know how to parse request %s %s" % (hr.method, hr.path))



def build_response(dr):
    """ Build an HTTP response from an abstract node_core direct response object """

    if isinstance(dr, ncore.GenericOk):
        return HttpResponse(200)

    if isinstance(dr, ncore.NodeList):
        body = build_node_descriptor_list(dr.nodes)
        return HttpResponse(200, body)

    else:
        raise RuntimeError("Do not know how to build response for %s" % (dr,) )


# Actually Send Requests

def send_message(msg):
    """ Send a message to another node """
    logger.debug("Sending message: %s" % (msg,))
    hr = build_request(msg)
    send_request(hr)


def send_request(hr):
    """ Actually send a request to a server via HTTP """

    conn = httplib.HTTPConnection(hr.host, hr.port)
    conn.request(hr.method, hr.path, hr.body)
    logger.debug("Sent request: %s:%d %s %s '%s'" %
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
        raise RuntimeException("Got bad response: %s" % response.status)

    logger.debug("Got OK response: %s %s" % (hr.method, hr.path))


# Actually Run as a Server

server_node_core = None     # Core decision module for server

class HttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    global server_node_core

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def do_PUT(self):
        self.handle_request("PUT")

    def handle_request(self, method):
        logger.debug("Receiving request: %s %s" % (method, self.path))
        content_length = int(self.headers.getheader('content-length', 0))
        body = self.rfile.read(content_length)

        msg = parse_request(HttpRequest(
                destination = server_node_core.descriptor,
                method = method,
                path = self.path,
                body = body))
        logger.debug("Parsed message: %s" % (msg,))

        action = server_node_core.handle_message(msg)

        self.send_response_for_action(action)
        for newmsg in action.new_messages:
            message_queue.put(newmsg)

    def send_response_for_action(self, action):
        hr = build_response(action)
        logger.debug("Responding with %s" % (action,))
        self.send_response(hr.status)
        self.end_headers()
        self.wfile.write(hr.body)

    def log_message(self, *args):
        """ Noop override to suppress normal request logging """
        return



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


# An outgoing message queue

message_queue = None

class MessageQueue:

    def __init__(self):
        self.outbox = Queue.Queue()
        self.thread = None

    def start(self):

        logger.debug("Starting message queue")
        def sender():
            while True:
                msg = self.outbox.get()
                send_message(msg)
                self.outbox.task_done()

        self.thread = threading.Thread(
                name="msg queue sender",
                target=sender)
        self.thread.daemon = True
        self.thread.start()

    def put(self, msg):
        self.outbox.put(msg)

    def stop(self):
        """ Waits until current messages are sent, then quits """
        logger.debug("Stopping message queue after empty...")
        self.outbox.join()
        logger.debug("Message queue empty, shutting down.")



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true",
            help="debug trace")
    parser.add_argument("host_port", metavar="host:port",
            help="external hostname (or IP) and port for this server")
    parser.add_argument("--join", metavar="host:port", default=None,
            help="another server to join")
    args = parser.parse_args()

    if args.verbose:
        ncore.logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    descriptor = ncore.NodeDescriptor(host_port=args.host_port)
    join_descriptor = ncore.NodeDescriptor(host_port=args.join) if args.join else None
    server_node_core = ncore.NodeCore(descriptor)

    # Start the webserver which handles incomming requests
    logger.debug("Starting HTTP server: %s, %s" % (descriptor, descriptor.rank))
    httpd = NodeServer((descriptor.host, descriptor.port), HttpRequestHandler)
    server_thread = threading.Thread(target = httpd.serve)
    server_thread.daemon = True
    server_thread.start()

    # Start the message queue to handle outgoing requests
    message_queue = MessageQueue()
    message_queue.start()

    def handler(signum, frame):
        logger.debug("Caught signal %d, stopping http server..." % signum)
        httpd.stop()
        message_queue.stop()
    signal.signal(signal.SIGINT, handler)

    # Join network
    if join_descriptor:
        joinmsg = ncore.Join(destination=join_descriptor, new_node=descriptor)
        send_message(joinmsg)

    # Wait for server thread to exit
    server_thread.join(100)
