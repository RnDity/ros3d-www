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
import logging

_log = logging.getLogger(__name__)

PROVIDER_CONNMAN = 1
PROVIDER_NETWORKMANAGER = 2

def network_provider(provider_type=PROVIDER_NETWORKMANAGER):
    # quick dbus init
    provider = None
    if provider_type == PROVIDER_CONNMAN:
        _log.debug('using connman provider')
        from ros3dui.system.network.connman import get_connman_provider
        provider = get_connman_provider()
    elif provider_type == PROVIDER_NETWORKMANAGER:
        _log.debug('using networkmanager provider')
        from ros3dui.system.network.networkmanager import get_networkmanager_provider
        provider = get_networkmanager_provider()
    else:
        raise RuntimeError('Unknown provider type: %d' % (provider_type))

    return provider

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    import sys

    provider_type = PROVIDER_NETWORKMANAGER
    provider = network_provider(provider_type)
    ifaces = provider.list_interfaces()
    logging.debug('ifaces: %s', ifaces)
