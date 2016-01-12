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
from ros3dui.system.network import network_provider
from ros3dui.system.camera import get_camera_manager, CameraManagerError
from ros3dui.system.util import ConfigLoader, get_hostname
from ros3dui.system.services import ServiceReloader
from ros3dui.system.rest_client import DevControllerRestClient, convert_to_simple_value_format
import tornado.web
import tornado.template
from tornado.escape import parse_qs_bytes
import logging
import os.path
import os
from functools import partial
from subprocess import call
from threading import Timer

_log = logging.getLogger(__name__)


def widget_render(ldr, widget):
    """Render a form widget using a template loder and widget
    description. Widget description is a dict with fields:
    - id - used as field id/name
    - value - field value or None
    - type - dropdown/input/password/plain etc.

    Dropdown widgets will produce a dropbox. Input/password produce a
    one line text input (password uses masking characters). Plain,
    outputs entry's value as it is.
    """
    _log.debug('render widget: %s', widget)
    tmpl = ldr.load('widgets.html')
    return tmpl.generate(entry=widget)


class SystemSettingsHandler(tornado.web.RequestHandler):

    aladin_modes_get = {'READ_ONLY':'Read only',
                        'INTERACTIVE':'Interactive'}
    aladin_modes_post = {v: k for k, v in aladin_modes_get.items()}

    def initialize(self, app):
        self.app = app

    def get(self):
        ldr = self.app.get_template_loader()
        tmpl = ldr.load('system_settings.html')

        config = ConfigLoader()
        rig = config.get_system()
        if not rig:
            rig = None
        system_entries = [
            dict(name='Assigned Rig', value=rig, type='input', id='assigned_rig')
        ]
        if self.app.mode == self.app.MODE_KR:
            aladin = config.get_aladin()
            system_entries.append(dict(name='Aladin control mode',
                                       value=SystemSettingsHandler.aladin_modes_get[aladin],
                                       type='dropdown',
                                       id='controll_aladin',
                                       options=list(SystemSettingsHandler.aladin_modes_get.values())))

        self.write(tmpl.generate(system_entries=system_entries,
                                 configuration_active=True,
                                 widget_render=partial(widget_render, ldr)))


    def post(self):
        _log.debug('configuration set: %s' , self.request)
        _log.debug('body: %s', self.request.body)

        # parse request
        arguments = parse_qs_bytes(self.request.body, keep_blank_values=False)
        _log.debug('arguments: %s', arguments)

        if arguments.has_key('assigned_rig') and arguments['assigned_rig'][0]:
            rig = arguments['assigned_rig'][0]
            _log.debug('set assigned rig to: %s', rig)
        else:
            rig = None

        if (self.app.mode == self.app.MODE_KR) and arguments['controll_aladin'][0]:
            aladin = self.aladin_modes_post[arguments['controll_aladin'][0]]

        def get_arg(arg):
            if arguments.has_key(arg):
                return arguments[arg][0]
            else:
                return None

        # services in need of reload
        need_reload = []

        config = ConfigLoader()
        if rig != config.get_system():
            config.set_system(rig)
            # reload controller service
            need_reload.append(ServiceReloader.SERVICE_CONTROLLER)

        if self.app.mode == self.app.MODE_KR:
            if aladin != config.get_aladin():
                config.set_aladin(aladin)
                need_reload.append(ServiceReloader.SERVICE_SERVO)

        # update configuration file
        config.write()

        if need_reload:
            _log.info('services needing reload: %s', need_reload)
            ServiceReloader.reload(need_reload)
            _log.info('reload complete')

        self.redirect('/?config_applied=1')


class NetworkSettingsHandler(tornado.web.RequestHandler):
    def initialize(self, app):
        self.app = app

    def get(self):
        ldr = self.app.get_template_loader()
        tmpl = ldr.load('network_settings.html')

        config = ConfigLoader()
        net = network_provider().list_interfaces()
        wired = net['wired'][0]
        if bool(net.get('wireless', [])):
            wireless = net['wireless'][0]
        else:
            wireless = None

        # format IP address assignment method properly
        def _convert_ip_method(in_method):
            """Convert passed IP method to a value that is suitable for presentation"""
            conv_method = {
                'dhcp': 'DHCP',
                'static': 'Static'
            }
            return conv_method.get(in_method, 'Unknown')

        _log.debug('first wired interface: %s', wired)

        if wired['online']:
            src = 'ipv4'
        else:
            src = 'ipv4conf'
        eth_address = wired[src].get('address', None)
        eth_netmask = wired[src].get('netmask', None)
        eth_gateway = wired[src].get('gateway', None)
        eth_method = _convert_ip_method(wired[src].get('method', 'dhcp'))

        # setup wired interface
        network_entries = {
            'wired': [
                dict(name='IPv4 Address', value=eth_address,
                     type='input', id='eth_ipv4_address'),
                dict(name='IPv4 Mask', value=eth_netmask,
                     type='input', id='eth_ipv4_netmask'),
                dict(name='IPv4 Gateway', value=eth_gateway,
                     type='input', id='eth_ipv4_gateway'),
                dict(name='IPv4 Method', value=eth_method,
                     type='dropdown', id='eth_ipv4_method',
                     options=['DHCP', 'Static'])
            ],
            'wireless': []
        }

        if wireless:
            if wireless['online']:
                src = 'ipv4'
            else:
                src = 'ipv4conf'
            wifi_address = wireless[src].get('address', None)
            wifi_netmask = wireless[src].get('netmask', None)
            wifi_gateway = wireless[src].get('gateway', None)
            wifi_method = _convert_ip_method(wireless[src].get('method', 'dhcp'))

            if wireless['wificonf']:
                wifi_ap = wireless['wificonf'].get('name', None)
                wifi_psk = wireless['wificonf'].get('wpa-psk', None)
            else:
                wifi_ap = None
                wifi_psk = None

            wireless_entry = [
                dict(name='Access Point', value=wifi_ap,
                     type='input', id='wifi_ap_name'),
                dict(name='WPA Password', value=wifi_psk,
                     type='password', id='wifi_psk_pass'),
                dict(name='IPv4 Address', value=wifi_address,
                     type='input', id='wifi_ipv4_address'),
                dict(name='IPv4 Mask', value=wifi_netmask,
                     type='input', id='wifi_ipv4_netmask'),
                dict(name='IPv4 Gateway', value=wifi_gateway,
                     type='input', id='wifi_ipv4_gateway'),
                dict(name='IPv4 Method', value=wifi_method,
                     type='dropdown', id='wifi_ipv4_method',
                     options=['DHCP', 'Static'])
            ]
        else:
            wireless_entry = [
                dict(name='Status', value='No device')
            ]
        if self.app.mode == self.app.MODE_KR:
            network_entries['wireless'] = wireless_entry

        self.write(tmpl.generate(network_entries=network_entries,
                                 configuration_active=True,
                                 widget_render=partial(widget_render, ldr)))


    def post(self):
        _log.debug('configuration set: %s' , self.request)
        _log.debug('body: %s', self.request.body)

        # parse request
        arguments = parse_qs_bytes(self.request.body, keep_blank_values=False)
        _log.debug('arguments: %s', arguments)

        wired_config = {}
        wireless_config = {}

        def get_ip_config(prefix):
            if arguments.has_key(prefix + '_ipv4_method'):
                method = arguments[prefix + '_ipv4_method'][0].lower()
                if method not in ['dhcp', 'static']:
                    # incorrect method
                    # TODO: raise exception
                    _log.error('incorrect method: %s', method)

                ipv4_config = {
                    'method': method
                }

                static_method_keys = [prefix + '_ipv4_address',
                                      prefix + '_ipv4_netmask',
                                      prefix + '_ipv4_gateway']
                if method == 'static':
                    if all([arguments.has_key(k) for k in static_method_keys]) == False:
                        # missing confgiuration
                        # TODO: raise exception
                        _log.error('incorrect network configuration: %s', arguments)
                    else:
                        ipv4_config['address'] = arguments[prefix + '_ipv4_address'][0]
                        ipv4_config['netmask'] = arguments[prefix + '_ipv4_netmask'][0]
                        ipv4_config['gateway'] = arguments[prefix + '_ipv4_gateway'][0]
                return ipv4_config
            else:
                # TODO: raise exception
                _log.error('IPv4 method not specified in arguments: %s', arguments)
            return None

        wired_config['ipv4'] = get_ip_config('eth')
        wireless_config['ipv4'] = get_ip_config('wifi')

        def get_arg(arg):
            if arguments.has_key(arg):
                return arguments[arg][0]
            else:
                return None

        wireless_config['name'] = get_arg('wifi_ap_name')
        wireless_config['password'] = get_arg('wifi_psk_pass')

        net = network_provider()
        net_config = {
            'wired': [wired_config],
        }
        if self.app.mode == self.app.MODE_KR:
            net_config['wireless'] = [wireless_config]

        net.set_config(net_config)

        config = ConfigLoader()
        config.write()

        self.redirect('/?config_applied=1')


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, app):
        self.app = app

    def _uptime(self):
        with open('/proc/uptime') as inf:
            secs = float(inf.read().strip().split()[0])

        days, rest = divmod(int(secs), 3600 * 24)
        hours, rest = divmod(rest, 3600)
        minutes, rest = divmod(rest, 60)
        seconds = rest

        uptime = '{}d {}h {}m {}s'.format(days, hours,
                                          minutes, seconds)
        _log.debug('system uptime: %s', str(uptime))
        return str(uptime)

    def _net(self):
        data = network_provider().list_interfaces()

        network_entries = {
           'wired': []
        }
        if self.app.mode == self.app.MODE_KR:
            network_entries['wireless'] = []

        # we're intersted in wired and wireless interfaces only
        for itype in network_entries.keys():
            if itype not in data:
                # device status is present in interface data, assuming
                # that there should be one add a status info that
                # there is 'no device' at this time
                network_entries[itype].append(dict(name='State', value='No device'))
                _log.debug('interface type %s not in available interfaces',
                           itype)
                continue

            entry = network_entries[itype]
            # expecting only one interface
            if len(data[itype]) > 1:
                _log.error('more than 1 interface of type %s', itype)

            idata = data[itype][0]
            _log.debug('interface data: %s', idata)

            ipv4 = idata.get('ipv4', None)
            # first interface name
            entry.append(dict(name='Interface', value=idata['device']))
            # MAC address comes next
            entry.append(dict(name='MAC Address', value=idata['mac']))
            # interface status
            if idata['online']:
                entry.append(dict(name='State', value='Up'))

                # add connected access point entry
                if idata['type'] == 'wireless':
                    entry.append(dict(name='Access Point', value=idata['name']))
            else:
                # may not be online but still usable with local addressing
                if ipv4 and ipv4['address'].startswith('169.254'):
                    entry.append(dict(name='State', value='Up/Local'))
                else:
                    entry.append(dict(name='State', value='Down'))

            # now fill IPv4 status
            if ipv4:
                # address first
                entry.append(dict(name='IPv4 Address', value=ipv4['address']))
                # network mask
                entry.append(dict(name='IPv4 Mask', value=ipv4['netmask']))
                # gateway
                entry.append(dict(name='IPv4 Gateway', value=ipv4.get('gateway', 'Not set')))
                # IP address source, this can be either DHCP, static,
                # or auto link-local. The connman provider returns
                # DHCP when link-local address was configured
                if ipv4['method'] == 'dhcp':
                    method = 'DHCP'
                    # override address source for link local addresses
                    if ipv4['address'].startswith('169.254'):
                        _log.debug('IP %s like link local address', ipv4['address'])
                        method = 'Link Local'
                else:
                    method = 'Static'
                entry.append(dict(name='Address Source', value=method))

        _log.debug('network entries: %s', network_entries)
        return network_entries

    def get(self):
        _log.debug("get: %r", self.request)

        config_applied = self.get_argument('config_applied', False)
        if config_applied == '1':
            config_applied = True

        reboot_applied = self.get_argument('reboot_applied', False)
        if reboot_applied == '1':
            reboot_applied = True

        ldr = self.app.get_template_loader()
        tmpl = ldr.load('status.html')

        config = ConfigLoader()
        rig = config.get_system()
        if not rig:
            rig = 'None'

        hostname = get_hostname()
        if not hostname:
            hostname = 'ros3d'

        system_entries= [
            dict(name='Hostname', value=hostname),
            dict(name='Assigned Rig', value=rig)
        ]

        if self.app.mode == Application.MODE_KR:
            aladin = config.get_aladin()
            system_entries.append(dict(name='Aladin Control Mode',
                                       value=SystemSettingsHandler.aladin_modes_get[aladin]))

        system_entries.append(dict(name='Uptime', value=self._uptime()))
        network_entries = self._net()
        camera_entries = [
                dict(name='Cam 1', value='Inactive'),
                dict(name='Cam 2', value='Active')
                ]
        camera_entries = self._cam()
        self.write(tmpl.generate(system_entries=system_entries,
                                 network_entries=network_entries,
                                 camera_entries=camera_entries,
                                 config_applied=config_applied,
                                 reboot_applied=reboot_applied,
                                 system_active=True,
                                 widget_render=partial(widget_render, ldr)))

    def _cam(self):
        entries = {}
        try:
            camera_data = get_camera_manager().get_details()
        except CameraManagerError:
            entries['Error']= [dict(name='Controller service unavailable',
                value='')]
        else:
            if not camera_data:
                entries['Warning'] = [dict(name='No cameras found', value='')]
            else:
                for idx, camera in enumerate(camera_data):
                    name = 'Camera ' + str(idx+1)
                    entries[name] = []
                    entries[name].append(camera)
        return entries


class RebootHandler(tornado.web.RequestHandler):
    def initialize(self, app):
        self.app = app

    def get(self):
        _log.debug("get, reboot request: %r", self.request)
        t = Timer(1, self.reboot)
        t.start()
        self.redirect('/?reboot_applied=1')

    def reboot(self):
        call(["reboot", "now"])


class SnapshotsHandler(tornado.web.RequestHandler):
    """Handler for parameter snapshots requests"""

    def initialize(self, app):
        self.app = app

    def get(self):
        _log.debug("get snapshots request")

        ldr = self.app.get_template_loader()
        tmpl = ldr.load('snapshots.html')

        rest = DevControllerRestClient()
        snapshots = rest.get_snapshots_list()

        self.write(tmpl.generate(snapshots=snapshots, parameters_active=True))

    def delete(self):
        rest = DevControllerRestClient()
        rest.delete_snapshots()


class ShotcalcHandler(tornado.web.RequestHandler):
    """Handler for main site of shot calculator"""

    def initialize(self, app):
        self.app = app

    def get(self):
        _log.debug("shotcalc request for main site")

        ldr = self.app.get_template_loader()
        try:
            tmpl = ldr.load('shotcalc.html')
        except IOError:
            tmpl = ldr.load('shotcalc-error.html')

        self.write(tmpl.generate(parameters_active=True))


class SnapshotDownloadHandler(tornado.web.RequestHandler):
    """Handler for parameter snapshots requests"""

    def get(self, snapshot_id):
        _log.debug("get snapshot request, id %s", snapshot_id)

        rest = DevControllerRestClient()
        snapshot = rest.get_snapshot(snapshot_id)

        self.write(convert_to_simple_value_format(snapshot))


class Application(tornado.web.Application):
    MODE_KR = 1
    MODE_AO = 2

    def __init__(self, document_root, mode=MODE_KR):
        self.mode = mode
        self.template_root = os.path.join(document_root,
                                          'templates')
        self.static_root = os.path.join(document_root,
                                        'static')
        fonts_root = os.path.join(document_root, 'fonts')

        shotcalc_root = "/".join((document_root, 'shotcalc'))
        uris = [
            (r"/network_settings", NetworkSettingsHandler, dict(app=self)),
            (r"/system_settings", SystemSettingsHandler, dict(app=self)),
            (r"/status", MainHandler, dict(app=self)),
            (r"/reboot", RebootHandler, dict(app=self)),
            (r"/fonts/(.*)", tornado.web.StaticFileHandler, dict(path=fonts_root)),
            (r"/snapshots", SnapshotsHandler, dict(app=self)),
            (r"/snapshot/([0-9]+)", SnapshotDownloadHandler),
            (r"/shotcalc/", ShotcalcHandler, dict(app=self)),
            (r"/shotcalc/(.*)", tornado.web.StaticFileHandler,
             dict(path=shotcalc_root)),
            (r"/", MainHandler, dict(app=self)),
        ]

        super(Application, self).__init__(uris,
                                          autoreload=True,
                                          debug=True,
                                          static_path=self.static_root)

        _log.debug('loading templates from: %s', self.template_root)
        _log.debug('static files from: %s', self.static_root)
        # self.loader = tornado.template.Loader(template_root)

    def get_template_loader(self):
        return tornado.template.Loader(self.template_root)
