#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#

import dbus
import glib
from dbus.mainloop.glib import DBusGMainLoop
import logging


_log = logging.getLogger(__name__)


def _make_variant(string):
    """Convert Python string to DBus.String"""
    return dbus.String(string, variant_level=1)


def _extract_ip_data(props, key='IPv4'):
    """Extract IPv4/IPv6 data from service properties. The key can either
    be IPv4 (to extract current state) or IPv4.Configuration (to
    extract configuration).
    """
    ipv4 = {}
    # list of keys in original property set and the key used in
    # returned dict
    key_entries = [('Address', 'address'),
                   ('Netmask', 'netmask'),
                   ('Gateway', 'gateway'),
                   ('Method', 'method')]

    for orig_key, to_key in key_entries:
        if orig_key in props[key]:
            ipv4[to_key] = str(props[key][orig_key])
            if orig_key == 'Method':
                method = str(props[key][orig_key])
                if method == 'manual':
                    ipv4['method'] = 'static'
                elif method == 'dhcp':
                    ipv4['method'] = 'dhcp'
        else:
            ipv4[to_key] = None

    return ipv4


class ConnmanProvider(object):

    CONNMAN_SERVICE_NAME = 'net.connman'
    CONNMAN_MANAGER_IFACE = 'net.connman.Manager'
    CONNMAN_SERVICE_IFACE = 'net.connman.Service'

    def __init__(self):
        self.bus = dbus.SystemBus()
        cmobj = self.bus.get_object(self.CONNMAN_SERVICE_NAME, '/')
        self.cm = dbus.Interface(cmobj, self.CONNMAN_MANAGER_IFACE)

    def list_interfaces(self):
        # Connman service does not map directly to interface. A
        # visible AP can also be considered a service
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

            iface['type'] = str(props['Type'])

            if props['State'] in ['online', 'ready']:
                iface['online'] = True
            else:
                iface['online'] = False

            iface['device'] = str(props['Ethernet']['Interface'])
            iface['mac'] = str(props['Ethernet']['Address'])

            # skip interface that is not online
            if iface['online'] == True:
                iface['ipv4'] = _extract_ip_data(props, 'IPv4')

            iface['ipv4conf'] = _extract_ip_data(props, 'IPv4.Configuration')

            if service_type not in interface_data:
                interface_data[service_type] = []

            interface_data[service_type].append(iface)

        return interface_data

    def _find_service_of_type(self, service_type):
        """Find a service of matching type among connman services. Returns
        path to service or None"""
        _log.debug('find service of type: %s', service_type)
        services = self.cm.GetServices()

        for service in services:
            path, props = service
            _log.debug('check service %s of type %s', path, props['Type'])
            if props['Type'].lower() == service_type.lower():
                _log.debug('matching service of type %s: %s',
                           service_type, path)
                return path
        _log.info('service of type %s not found', service_type)
        return None

    def set_config(self, config):
        _log.debug('set configuration: %s', config)

        path = self._find_service_of_type('ethernet')
        _log.debug('service path: %s', path)
        self.set_service_config(path, config['wired'][0])

    def set_service_config(self, path, config):
        servobj = self.bus.get_object(self.CONNMAN_SERVICE_NAME, path)
        service = dbus.Interface(servobj, self.CONNMAN_SERVICE_IFACE)
        #props = dbus.Interface(servobj, 'org.freedesktop.DBus.Properties')

        _log.debug('service properties: %s', service.GetProperties())

        ipv4_config = {}

        if config['ipv4']['method'].lower() == 'static':
            ipv4_config['Method'] = _make_variant('manual')
            ipv4_config['Address'] = _make_variant(config['ipv4']['address'])
            ipv4_config['Netmask'] = _make_variant(config['ipv4']['netmask'])
            ipv4_config['Gateway'] = _make_variant(config['ipv4']['gateway'])
        elif config['ipv4']['method'].lower() == 'dhcp':
            ipv4_config['Method'] = _make_variant('dhcp')


        _log.debug('setting configuration: %s', ipv4_config)
        service.SetProperty('IPv4.Configuration', ipv4_config)


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
