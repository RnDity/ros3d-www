#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#
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
        from ros3dkrui.system.network.connman import get_connman_provider
        provider = get_connman_provider()
    elif provider_type == PROVIDER_NETWORKMANAGER:
        _log.debug('using networkmanager provider')
        from ros3dkrui.system.network.networkmanager import get_networkmanager_provider
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
