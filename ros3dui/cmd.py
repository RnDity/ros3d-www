#
# Copyright (c) 2015 Open-RnD Sp. z o.o.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import
from ros3dui.web import Application
from ros3dui.system.util import ConfigLoader
from ros3dui.system.services import ServiceReloader
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
    parser.add_argument('-c', '--config-path',
                        help='Configuration file path, ' \
                        'default: {}'.format(ConfigLoader.CONFIG_PATH),
                        default=None)
    parser.add_argument('--helpers-dir', help='Path to helper tools directory',
                        default=None)
    parser.add_argument('-i', '--ia', help="Set if running on Image Analyser", action="store_true")
    parser.add_argument('document_root', help='Document root')
    return parser.parse_args()


def main():
    opts = parse_arguments()

    level = logging.INFO
    if opts.debug:
        level = logging.DEBUG
    logging.basicConfig(level=level)

    if opts.config_path:
        ConfigLoader.set_config_location(opts.config_path)

    if not opts.document_root:
        logging.error('Document root not provided')
        raise SystemExit(1)

    logging.debug('configuration at: %s', ConfigLoader.CONFIG_PATH)

    if opts.helpers_dir:
        ServiceReloader.set_helpers_dir(opts.helpers_dir)

    if opts.ia:
        logging.error('Image Analyzer mode')
        app = Application(opts.document_root, mode=Application.MODE_AO)
    else:
        app = Application(opts.document_root)

    logging.debug('listening on port %d', opts.http_port)
    app.listen(opts.http_port)

    logging.debug('starting...')
    IOLoop.instance().start()



