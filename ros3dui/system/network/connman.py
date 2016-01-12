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

import dbus
import glib
from dbus.mainloop.glib import DBusGMainLoop
import logging


_log = logging.getLogger(__name__)


def _make_variant(string):
    """Convert Python string to DBus.String"""
    return dbus.String#
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
        # _log.debug('services: %s', services)

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

            iface = {}
            iface['type'] = str(props['Type']).lower()
            _log.debug('interface type %s', iface['type'])
            # convert interface type to wifi/wireless
            if iface['type'] == 'ethernet':
                iface['type'] = 'wired'
            elif iface['type'] == 'wifi':
                iface['type'] = 'wireless'
            _log.debug('updated interface type %s', iface['type'])

            service_type = iface['type']

            # service name, for ethernet this will be wired, for wifi
            # this contains SSID
            iface['name'] = str(props['Name'])

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

    def _find_service(self, predicate):
        """Find a service for which the predicate returns True. Returns path
        to service or None.
        """
        services = self.cm.GetServices()

        for service in services:
            path, props = service
            if predicate(props) == True:
                _log.debug('matching service: %s', path)
                return path
        _log.info('matching service not found')
        return None

    def _find_service_of_type(self, service_type):
        """Find a service of matching type among connman services. Returns
        path to service or None"""
        _log.debug('find service of type: %s', service_type)

        def _match_type(props):
            _log.debug('check service of type %s', props['Type'])
            if props['Type'].lower() == service_type.lower():
                _log.debug('matching service of type %s',
                           service_type)
                return True
            return False

        return self._find_service(_match_type)

    def _find_service_of_name(self, service_name):
        """Find a service of matching name among connman services. Returns
        path to service or None"""
        _log.debug('find service of name: \'%s\'', service_name)

        def _match_name(props):
            _log.debug('check service of name %s', props['Name'])
            if props['Name'] == service_name:
                _log.debug('matching service of name \'%s\'',
                           service_name)
                return True
            return False

        return self._find_service(_match_name)

    def set_config(self, config):
        _log.debug('set configuration: %s', config)

        for key, conf in config.items():
            if key == 'wired':
                path = self._find_service_of_type('ethernet')
            elif key == 'wireless':
                path = self._find_service_of_name(conf[0]['name'])

            _log.debug('service path: %s', path)
            if path:
                self.set_service_config(path, conf[0])
            else:
                _log.error('service %s not configured', key)

    def set_service_config(self, path, config):
        _log.debug('set config for service %s to: %s', path, config)
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

        # if 'name' in config:
        #     _log.debug('setting name to %s', config['name'])
        #     service.SetProperty('Name', _make_variant(config['name']))
        if 'password' in config:
            _log.debug('setting password to %s', config['password'])
            service.SetProperty('Passphrase', _make_variant(config['password']))


def get_connman_provider():
    """Get an instance of ConnmanProvider"""
    glib.threads_init()
    dbus.mainloop.glib.threads_init()

    DBusGMainLoop(set_as_default=True)

    return ConnmanProvider()

