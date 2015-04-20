#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#

from __future__ import absolute_import

import dbus
import glib
from dbus.mainloop.glib import DBusGMainLoop
import logging
from uuid import uuid4


_log = logging.getLogger(__name__)


def _make_variant(string):
    """Convert Python string to DBus.String"""
    return dbus.String


def _array_to_string(dbus_array):
    """Converts dbus array to string"""
    out = ''.join(chr(byte) for byte in dbus_array)
    _log.debug('converted string: %s', out)
    return out

def _string_to_array(string):
    """Converts string to dbus Byte array"""
    out = [dbus.Byte(c) for c in string]
    _log.debug('converted string %s to array: %s', string, out)
    return out

def _prefix_to_netmask(prefix):
    """Convert IP network mask prefix length to netmask in dot-number
    notation."""
    mask_len = 32
    if prefix > mask_len or prefix < 0:
        raise RuntimeError('Incorrect prefix length %d' % (prefix))

    _log.debug('convert prefix %d to netmask', prefix)

    mask = (2 ** prefix - 1) << (mask_len  - prefix)
    ens = []
    for shift in range(0, mask_len, 8):
        ens.append('%d' % ((mask >> shift) & 0xff))
    as_netmask = '.'.join(reversed(ens))

    _log.debug('prefix %d = netmask %s', prefix, as_netmask)
    return as_netmask


def _netmask_to_prefix(netmask):
    """Converts netmask in dot-number notation to prefix length"""
    from collections import Counter
    _log.debug('convert netmask: %s', netmask)
    binary = bin(_ip_to_num(netmask))
    c = Counter(binary)
    prefix = c['1']
    _log.debug('converted netmask %s to prefix: %d', netmask, prefix)
    return prefix


def _num_to_ip(ip_in_num):
    """Converts IPv4 address expressed as integer in network byte order to
    dot-number notation"""
    import socket
    import struct
    # since IP is already presented as integer encoded in network byte
    # order, struct pack uses native byte ordering
    ip = socket.inet_ntoa(struct.pack('I', ip_in_num))
    _log.debug('converted IP address: %s', ip)
    return ip


def _ip_to_num(ip):
    """Converts IPv4 address expressed in dot-number notation to byte order integer"""
    import socket
    import struct
    # inet_aton returns packed integer in byte order, no need to
    # convert to host ordering as we want to return network order
    num = struct.unpack('I', socket.inet_aton(ip))[0]
    _log.debug('converted IP address %s: %d', ip, num)
    return num

class PropertiesWrapper(object):
    def __init__(self, busobj):
        _log.debug('properties wrapper for %s @ %s',
                   busobj.dbus_interface, busobj.object_path)
        self.busobj = busobj

    def __getattr__(self, key):
        _log.debug('get property %s', key)
        return self.busobj.Get(self.busobj.dbus_interface,
                               key,
                               dbus_interface=dbus.PROPERTIES_IFACE)

NM_DEVICE_TYPE_ETHERNET = 1
NM_DEVICE_TYPE_WIFI = 2

# operational
NM_DEVICE_STATE_ACTIVATED = 100
# no carrier
NM_DEVICE_STATE_UNAVAILABLE = 20
#
NM_DEVICE_STATE_DISCONNECTED = 30

NM_CONNECTION_TYPE_ETH = '802-3-ethernet'
NM_CONNECTION_TYPE_WIFI = '802-11-wireless'

NM_SECURITY_TYPE_WIFI = '802-11-wireless-security'
NM_SECURITY_WIFI_KEY_MGMT = 'key-mgmt'
NM_SECURITY_KEY_MGMT_WPA_PSK = 'wpa-psk'
NM_SECURITY_WPA_PSK = 'psk'

class NetworkManagerProvider(object):

    NM_SERVICE_NAME = 'org.freedesktop.NetworkManager'
    NM_SERVICE_PATH = '/org/freedesktop/NetworkManager'
    NM_SETTINGS_PATH = '/org/freedesktop/NetworkManager/Settings'
    NM_MANAGER_IFACE = 'org.freedesktop.NetworkManager'
    NM_SETTINGS_IFACE = 'org.freedesktop.NetworkManager.Settings'
    NM_CONNECTION_IFACE = 'org.freedesktop.NetworkManager.Settings.Connection'
    NM_DEVICE_IFACE = 'org.freedesktop.NetworkManager.Device'
    NM_DEVICE_WIRED_IFACE = 'org.freedesktop.NetworkManager.Device.Wired'
    NM_DEVICE_WIRELESS_IFACE = 'org.freedesktop.NetworkManager.Device.Wireless'
    NM_IP4CONFIG_IFACE = "org.freedesktop.NetworkManager.IP4Config"
    NM_ACCESS_POINT_IFACE = "org.freedesktop.NetworkManager.AccessPoint"

    def __init__(self):
        self.bus = dbus.SystemBus()
        nmobj = self.bus.get_object(self.NM_SERVICE_NAME,
                                    self.NM_SERVICE_PATH)
        self.nm = dbus.Interface(nmobj, self.NM_MANAGER_IFACE)

    def _get_bus_iface(self, devpath, iface):
        """Get proxy to interface and proxy for accessing interface properties
        for bus object at path `devpath` and interface `iface`
        """
        devobj = self.bus.get_object(self.NM_SERVICE_NAME,
                                    devpath)
        dev = dbus.Interface(devobj, iface)
        return dev, PropertiesWrapper(dev)

    def _get_device(self, devpath):
        """Proxy to device interface and it's properties"""
        return self._get_bus_iface(devpath,
                                   self.NM_DEVICE_IFACE)

    def _get_wired_device(self, devpath):
        """Proxy to wired device inteface and it's properties"""
        return self._get_bus_iface(devpath,
                                   self.NM_DEVICE_WIRED_IFACE)

    def _get_wireless_device(self, devpath):
        """Proxy to wireless device and it's properties"""
        return self._get_bus_iface(devpath,
                                   self.NM_DEVICE_WIRELESS_IFACE)

    def _get_ipv4_data(self, ipconfpath):
        """Dump IPv4 data into a dictionary with keys:
        - address
        - netmask
        - gateway
        - method (static|dhcp)
        """
        _log.debug('extract IP configuratin at path %s', ipconfpath)
        ipconf, props = self._get_bus_iface(ipconfpath,
                                            self.NM_IP4CONFIG_IFACE)
        ipv4 = {}
        adata = props.Addresses
        # expecting a single IP address
        if len(adata) < 1:
            _log.error('no IP address?')
            return None

        # Addresses - aau
        # Essentially: [(addr, prefix, gateway), (addr, prefix, gateway), ...]
        _log.debug('addresses: %s', adata)
        addr = adata[0][0]
        prefix = adata[0][1]
        gateway = adata[0][2]
        ipv4['address'] = _num_to_ip(addr)
        ipv4['netmask'] = _prefix_to_netmask(prefix)
        ipv4['gateway'] = _num_to_ip(gateway)
        _log.debug('IPv4 state: %s', ipv4)
        return ipv4

    def _dump_wireless_info(self, devpath):
        """Dump information about wifi connection into a dict with keys:
        - name - connected AP name
        - strength - signal strength
        - bitrate - current bitrate"""
        wifi, props = self._get_wireless_device(devpath)

        active_ap = props.ActiveAccessPoint

        ap, approps = self._get_bus_iface(active_ap,
                                          self.NM_ACCESS_POINT_IFACE)
        ssid = _array_to_string(approps.Ssid)
        _log.debug('AP ssid: %s', ssid)
        wifi_info = {
            'name': ssid,
            'strength': int(approps.Strength),
            'bitrate': int(props.Bitrate)
        }
        return wifi_info

    def _get_wireless_conf(self, devpath):
        """Dump wifi configuration. Produces a dict with keys:
        - name - selected AP SSID
        - security - none|wpa-psk|..
        - wpa-psk - WPA PSK

        or None if no wifi confguration is defined"""

        settings = self._find_settings_of_type(NM_CONNECTION_TYPE_WIFI)

        if len(settings) == 0:
            _log.warning('no settings found')
            return None

        conf = settings[0]
        _log.debug('settings: %s', conf)

        siface, props = self._get_bus_iface(conf,
                                            self.NM_CONNECTION_IFACE)
        data = siface.GetSettings()

        wificonf = {}

        _log.debug('got wifi settings: %s', data)

        ap = _array_to_string(data[NM_CONNECTION_TYPE_WIFI]['ssid'])
        _log.debug('AP: %s', ap)

        wificonf['name'] = ap

        if data.has_key(NM_SECURITY_TYPE_WIFI):
            security = siface.GetSecrets(NM_SECURITY_TYPE_WIFI)
            _log.debug('security data: %s', security)
            key = data[NM_SECURITY_TYPE_WIFI][NM_SECURITY_WIFI_KEY_MGMT]
            wificonf['security'] = str(key)
            if key == NM_SECURITY_KEY_MGMT_WPA_PSK:
                wificonf['wpa-psk'] = security[NM_SECURITY_TYPE_WIFI][NM_SECURITY_WPA_PSK]
                _log.debug('WPA PSK: %s', wificonf['wpa-psk'])

        _log.debug('wifi conf: %s', wificonf)
        return wificonf

    def _dump_device(self, dev, props):
        iface = {}
        devtype = props.DeviceType

        # convert interface type to wifi/wireless
        if devtype == NM_DEVICE_TYPE_ETHERNET:
            iface['type'] = 'wired'
            wired, wprops = self._get_wired_device(dev.object_path)
            iface['mac'] = str(wprops.HwAddress)
        elif devtype == NM_DEVICE_TYPE_WIFI:
            iface['type'] = 'wireless'
            wireless, wprops = self._get_wireless_device(dev.object_path)
            iface['mac'] = str(wprops.HwAddress)
            iface['wificonf'] = self._get_wireless_conf(dev.object_path)
        else:
            # skip all other interfaces
            return None

        _log.debug('updated interface type %s', iface['type'])

        service_type = iface['type']

        if props.State == NM_DEVICE_STATE_ACTIVATED:
            iface['online'] = True

            # grab access point name for active wireless interface
            if devtype == NM_DEVICE_TYPE_WIFI:
                wifi_info = self._dump_wireless_info(dev.object_path)
                _log.debug('appending wireless info: %s', wifi_info)
                iface.update(wifi_info)
        else:
            iface['online'] = False

        iface['device'] = str(props.Interface)

        # dump IPv4 status for interfaces that are online
        if iface['online'] == True:
            ipconfpath = props.Ip4Config
            _log.debug('IPv4 config at %s', ipconfpath)
            iface['ipv4'] = self._get_ipv4_data(ipconfpath)
            method = 'dhcp'
            if props.Dhcp4Config == '/':
                # no dhcp configuration, meaning manually configured
                # interface
                method = 'static'
            iface['ipv4']['method'] = method

        return iface

    def list_interfaces(self):
        devices = self.nm.GetDevices()
        _log.debug('devices: %s', devices)

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
        for devpath in devices:
            dev, props = self._get_device(devpath)
            _log.debug('dev: %s', props.Interface)
            _log.debug('device type: %d', props.DeviceType)

            iface = self._dump_device(dev, props)

            _log.debug('interface data: %s', iface)

            if iface:
                iftype = iface['type']
                if iftype not in interface_data:
                    interface_data[iftype] = []
                interface_data[iftype].append(iface)

        return interface_data

    def _find_settings(self, predicate):
        """Find settings for which the predicate returns True. Returns a list of paths
        to settings.
        """
        settings, props = self._get_bus_iface(self.NM_SETTINGS_PATH,
                                              self.NM_SETTINGS_IFACE)

        matching = []
        for setting in settings.ListConnections():
            if predicate(setting) == True:
                _log.debug('matching service: %s', setting)
                matching.append(setting)
        _log.info('matching settings: %s', matching)
        return matching

    def _find_settings_of_type(self, service_type):
        """Find a setting of matching type among connman services. Returns
        path to service or None"""
        _log.debug('find service of type: %s', service_type)

        def _match_type(path):
            setting, props = self._get_bus_iface(path, self.NM_CONNECTION_IFACE)
            data = setting.GetSettings()
            _log.debug('check setting with data %s', data)
            if data['connection']['type'] == service_type:
                return True
            return False

        return self._find_settings(_match_type)

    def _remove_settings(self, paths):
        for srvpath in paths:
            _log.debug('removing settings %s', srvpath)
            conn, props = self._get_bus_iface(srvpath,
                                              self.NM_CONNECTION_IFACE)
            conn.Delete()


    def set_config(self, config):
        """Set network configuration. `config` is a dict like this:
        {
        'wired': {  # ethernet configuration
            'ipv4': {
                 'method': dhcp|static
                 'address': only if static
                 'netmask': only if static
                 'gateway': only if static
             }
        }
        'wireless' {
            'password': '...' # WPA PSK
            'ipv4': {
                 ... # same as above
             }
        }
        }
        """
        _log.debug('set configuration: %s', config)

        for key, conf in config.items():
            if key == 'wired':
                srvtype = NM_CONNECTION_TYPE_ETH
            elif key == 'wireless':
                srvtype = NM_CONNECTION_TYPE_WIFI
            paths = self._find_settings_of_type(srvtype)

            _log.debug('service path: %s', paths)
            if paths:
                # first remove all settings
                self._remove_settings(paths)

            # add new setting
            self._set_service_config(srvtype, conf[0])

    def _set_service_config(self, srvtype, config):
        _log.debug('set config for service %s to: %s', srvtype, config)

        settings, props = self._get_bus_iface(self.NM_SETTINGS_PATH,
                                              self.NM_SETTINGS_IFACE)

        srvconf = {
            'connection': {
                'type': srvtype,
                'id': None,
                'uuid': str(uuid4()),
                'autoconnect': True,
            },
            'ipv4': {
            },
            srvtype: {}
        }

        if srvtype == NM_CONNECTION_TYPE_ETH:
            srvconf['connection']['id'] = 'Wired connection'
            # Extra ethernet settings, currently none are supported
        elif srvtype == NM_CONNECTION_TYPE_WIFI:
            # use AP name as ID
            srvconf['connection']['id'] = config['name']
            # wifi settings
            srvconf[srvtype]['ssid'] = _string_to_array(config['name'])
            if config['password']:
                # setup WPA
                srvconf[srvtype]['security'] = NM_SECURITY_TYPE_WIFI
                # suppor WPA-PSK only
                sec = {
                    'key-mgmt': 'wpa-psk',
                    'psk': config['password']
                }
                srvconf['802-11-wireless-security'] = sec

        # IPv4 configuration
        if config['ipv4']['method'] == 'dhcp':
            srvconf['ipv4']['method'] = 'auto'
        else:
            srvconf['ipv4']['method'] = 'manual'
            srvconf['ipv4']['addresses'] = [
                [
                    dbus.UInt32(_ip_to_num(config['ipv4']['address'])),
                    dbus.UInt32(_netmask_to_prefix(config['ipv4']['netmask'])),
                    dbus.UInt32(_ip_to_num(config['ipv4']['gateway']))
                ]
            ]

        _log.debug('service config: %s', srvconf)
        path = settings.AddConnection(srvconf)
        _log.debug('settings added at path: %s', path)
        return


def get_networkmanager_provider():
    """Get an instance of NetworkManagerProvider"""
    glib.threads_init()
    dbus.mainloop.glib.threads_init()

    DBusGMainLoop(set_as_default=True)

    return NetworkManagerProvider()

