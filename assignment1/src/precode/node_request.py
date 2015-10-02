#!/usr/bin/python
# vim: set sts=4 sw=4 et:

import httplib

def sendPUT(hostname, port, key, value):

    conn = httplib.HTTPConnection(hostname, port)
    conn.request("PUT", "/%s" % key, value)

    # Must read response even if we don't do anything with it.
    # If we don't, the server will get broken pipe errors.
    #	1. Return without reading response
    #	2. Server might not be finish sending response yet.
    #	3. Library code here closes connection.
    #	4. Server code tries to finish writing to closed pipe.
    #	5. Broken pipe.
    response = conn.getresponse()
    data = response.read()


def sendGET(hostname, port, key):
    conn = httplib.HTTPConnection(hostname, port)
    conn.request("GET", "/%s" % key)
    response = conn.getresponse()
    data = response.read()

    return data
