#!/usr/bin/python
# vim: set sts=4 sw=4 et:

import time

print "Hello World!"

class Process:
    def __init__(self):
        self.counter = 0

    def run(self):
        while True:
            time.sleep(1)
            print "Still alive"
            self.counter = self.counter + 1


if __name__ == '__main__':
    proc = Process()
    proc.run()
