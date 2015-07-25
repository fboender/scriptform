#!/usr/bin/env python

import os

name = os.environ['name']
if not name:
    name = "world"

print "Hello, {0}!".format(name)
