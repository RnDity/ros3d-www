#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#

import dbus
import glib
from dbus.mainloop.glib import DBusGMainLoop
import logging


_log = logging.getLogger(__name__)

class ConnmanProvider(object):
    def __init__(self):
        self.bus = dbus.SystemBus()
        cmobj = self.bus.get_object('net.connman', '/')
        self.cm = dbus.Interface(cmobj, 'net.connman.Manager')

    def list_interfaces(self):
        # service corresponds to interface, wired/wireless/modem..
        services = self.cm.GetServices()
        _log.debug('services: %s', services)

        # dictionary, with interface type as key, keys are:
        # - wired
        # - wireless
        # for every interface type there is a list of
        # dictionaries with keys:
        # - name
        # - online (True/False)
        # - MAC
        # - IPv4 (dict with keys address, netmask, gateway)

        interface_data = {}
        for service in services:
            path, props = service
            # for key, prop in props.items():
            #     _log.debug('prop: %s', key)
            #     if prop is dict:
            #         _log.debug('entries: %s', prop.keys())
            #     else:
            #         _log.debug('value: %s', prop)

            _log.info('service path: %s', path)
            _log.debug('props: %s', props.keys())

            _log.info("service: %s", props['Name'])

            service_type = props['Name'].lower()
            iface = {}
            ipv4 = {}

            iface['name'] = str(props['Ethernet']['Interface'])
            iface['mac'] = str(props['Ethernet']['Address'])
            iface['type'] = str(props['Type'])

            if props['State'] == 'online':
                iface['online'] = True
            else:
                iface['online'] = False

            ipv4['address'] = str(props['IPv4']['Address'])
            ipv4['netmask'] = str(props['IPv4']['Netmask'])
            if 'Gateway' in props['IPv4']:
                ipv4['gateway'] = str(props['IPv4']['Gateway'])
            ipv4['method'] = str(props['IPv4']['Method'])

            iface['ipv4'] = ipv4
            if service_type not in interface_data:
                interface_data[service_type] = []

            interface_data[service_type].append(iface)

        return interface_data


def network_provider():
    # quick dbus init
    glib.threads_init()
    dbus.mainloop.glib.threads_init()
    DBusGMainLoop(set_as_default=True)

    return ConnmanProvider()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    provider = network_provider()
    ifaces = provider.list_interfaces()
    logging.debug('ifaces: %s', ifaces)
