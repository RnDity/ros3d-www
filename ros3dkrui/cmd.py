#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#

from __future__ import absolute_import
from ros3dkrui.web import Application
from tornado.ioloop import IOLoop
import logging
import sys


LISTEN_PORT = 9900

def main():
    logging.basicConfig(level=logging.DEBUG)
    # parse options

    app = Application(sys.argv[1])
    logging.debug('listening on port %d', LISTEN_PORT)
    app.listen(LISTEN_PORT)

    logging.debug('starting...')
    IOLoop.instance().start()



