#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#

from __future__ import absolute_import
from ros3dkrui.system.network import network_provider
import tornado.web
import tornado.template
import logging
import os.path

_log = logging.getLogger(__name__)


class SettingsHandler(tornado.web.RequestHandler):
    def initialize(self, app):
        self.app = app

    def get(self):
        _log.debug("SettingsHandler: %s" % json_encode(settings))
        self.write("%s" % json_encode(settings))
    def post(self):
        temp = json_decode(self.request.body)
        temp2 = {}
        for key in temp:
            _log.debug("key: %s, value: %s" % (key, temp[key]))
            settings[key] = temp[key]
            _log.debug("sett: %s" % settings[key])
            temp2[key] = settings[key]
        self.write("%s" % json_encode(temp2))


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
            'wired': [],
            'wireless': []
        }
        # we're intersted in wired and wireless interfaces only
        for itype in network_entries.keys():
            if itype not in data:
                _log.debug('interface type %s not in available interfaces',
                           itype)
                continue

            entry = network_entries[itype]
            # expecting only one interface
            if len(data[itype]) > 1:
                _log.error('more than 1 interface of type %s', itype)

            idata = data[itype][0]
            _log.debug('interface data: %s', idata)
            # first interface name
            entry.append(dict(name='Interface', value=idata['name']))
            entry.append(dict(name='MAC Address', value=idata['mac']))
            if idata['online']:
                entry.append(dict(name='State', value='Up'))
            else:
                entry.append(dict(name='State', value='Down'))

            ipv4 = idata.get('ipv4', None)
            if ipv4:
                entry.append(dict(name='IPv4 Address', value=ipv4['address']))
                entry.append(dict(name='IPv4 Mask', value=ipv4['netmask']))
                entry.append(dict(name='IPv4 Gateway', value=ipv4['gateway']))
                if ipv4['method'] == 'dhcp':
                    meth = 'DHCP'
                else:
                    method = 'Static'
                entry.append(dict(name='Address Source', value=meth))

        _log.debug('network entries: %s', network_entries)
        return network_entries

    def get(self):
        _log.debug("get: %r", self.request)
        ldr = self.app.get_template_loader()
        tmpl = ldr.load('status.html')

        system_entries= [
            dict(name='Hostname', value='ros3d-kr'),
            dict(name='Assigned Rig', value='None')
        ]
        system_entries.append(dict(name='Uptime', value=self._uptime()))
        network_entries = self._net()

        self.write(tmpl.generate(system_entries=system_entries,
                                 network_entries=network_entries))


class Application(tornado.web.Application):

    def __init__(self, document_root):

        self.template_root = os.path.join(document_root,
                                          'templates')
        self.static_root = os.path.join(document_root,
                                        'static')
        uris = [
            (r"/settings", SettingsHandler, dict(app=self)),
            (r"/status", MainHandler, dict(app=self)),
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
