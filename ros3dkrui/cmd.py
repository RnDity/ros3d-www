#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#
from __future__ import absolute_import
from ros3dkrui.web import Application
from tornado.ioloop import IOLoop
import logging
import argparse


DEFAULT_LISTEN_PORT = 9900


def parse_arguments():
    parser = argparse.ArgumentParser(description='Ros3D Web UI')
    parser.add_argument('--http-port', default=DEFAULT_LISTEN_PORT,
                        type=int,
                        help='HTTP Port, default: {}'.format(DEFAULT_LISTEN_PORT))
    parser.add_argument('-d', '--debug', action='store_true',
                        default=False)
    parser.add_argument('document_root', help='Document root')
    return parser.parse_args()


def main():
    opts = parse_arguments()

    level = logging.INFO
    if opts.debug:
        level = logging.DEBUG
    logging.basicConfig(level=logging.DEBUG)

    if not opts.document_root:
        logging.error('Document root not provided')
        raise SystemExit(1)

    app = Application(opts.document_root)
    logging.debug('listening on port %d', opts.http_port)
    app.listen(opts.http_port)

    logging.debug('starting...')
    IOLoop.instance().start()



