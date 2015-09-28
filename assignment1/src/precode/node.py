#!/usr/bin/python
# vim: set sts=4 sw=4 et:

import BaseHTTPServer
import time
import threading
import signal

MAX_CONTENT_LENGHT = 1024		# Maximum length of the content of the http request (1 kilobyte)
MAX_STORAGE_SIZE = 104857600	# Maximum total storage allowed (100 megabytes)

class Node:

    def __init__(self):
        self.map = dict()
        self.size = 0

    def get_value(self, key):
        return self.map.get(key)

    def put_value(self, key, value, size):
        self.size = self.size + size
        self.map[key] = value



class NodeHttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    global node
    node = Node()

    # Returns the
    def do_GET(self):
        key = self.path

        # TODO: distributed stores
        #   Divide key space.
        #   If this node is responsible for key, give response.
        #   If not, query next node.
        value = node.get_value(key)

        if value is None:
            self.sendErrorResponse(404, "Key not found")
            return

        # Write header
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()

        # Write Body
        self.wfile.write(value)

    def do_PUT(self):
        contentLength = int(self.headers['Content-Length'])

        if contentLength <= 0 or contentLength > MAX_CONTENT_LENGHT:
            self.sendErrorResponse(400, "Content body to large")
            return

        # TODO: distributed stores
        #   Divide key space.
        #   If this node is responsible for key, give response.
        #   If not, query next node.
        node.put_value(self.path, self.rfile.read(contentLength), contentLength)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def sendErrorResponse(self, code, msg):
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(msg)



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
