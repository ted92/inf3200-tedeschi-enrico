#!/usr/bin/python
# vim: set sts=4 sw=4 et:

import httplib

""" Common routines for parsing and sending HTTP reqests to nodes """

# HTTP request object

class Request:
    def __init__(self, method="GET", path="", body=""):
        self.method = method
        self.path = path
        self.body = body

# Abstract request objects

class RequestGetKey:
    def __init__(self, key):
        self.key = key

class RequestPutKey:
    def __init__(self, key, value):
        self.key = key
        self.value = value

# Parse and Build -- Convert between HTTP request and abstract types

def parse_request(method, path, body):
    """ Parses an HTTP method+path+body to a more abstract request object """
    # if method=="GET" and path.startswith("key/"):
    if method=="GET":
        key = path #[4:]
        return RequestGetKey(key)

    if method=="PUT":
        key = path #[4:]
        value = body
        return RequestPutKey(key, value)

def build_request(ar):
    """ Converts an abstract request object to an HTTP method+path+body """
    if isinstance(ar, RequestGetKey):
        # return Request(method="GET", path="key/"+ar.key)
        return Request(method="GET", path=ar.key)

    if isinstance(ar, RequestPutKey):
        return Request(method="PUT", path=ar.key, body=ar.value)


# Send a PUT request, to store a key-value pair
def sendPUT(hostname, port, key, value):

    conn = httplib.HTTPConnection(hostname, port)
    conn.request("PUT", key, value)

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


# Send a GET request, to look up a key
def sendGET(hostname, port, key):
    conn = httplib.HTTPConnection(hostname, port)
    conn.request("GET", key)
    response = conn.getresponse()

    status_code = response.status
    content_type = response.getheader("Content-Type")
    data = response.read()

    return (status_code, content_type, data)
