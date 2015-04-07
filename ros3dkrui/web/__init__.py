#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#

from __future__ import absolute_import
import tornado.web
import tornado.template
import logging
import os.path

_log = logging.getLogger(__name__)


class SettingsHandler(tornado.web.RequestHandler):
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

class SettingHandler(tornado.web.RequestHandler):
    def get(self, id):
        _log.debug("SettingHandler: %s : %s" % (id, json_encode(settings[id])))
        temp = { id : settings[id] }
        self.write("%s" % json_encode(temp))
    def post(self, id):
        temp = json_decode(self.request.body)
        settings[id] = temp[id]
        _log.debug("SettingHandler post: %s: %s" % (id, json_encode(settings[id])))
        self.write(json_encode({id : settings[id]}))

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

    def get(self):
        _log.debug("get: %r", self.request)
        ldr = self.app.get_template_loader()
        tmpl = ldr.load('status.html')

        status_entries=[
            dict(name='IP Address', value='192.168.0.1'),
            dict(name='Hostname', value='ros3d-kr'),
            dict(name='Assigned Rig', value='None')
        ]
        status_entries.append(dict(name='Uptime', value=self._uptime()))

        self.write(tmpl.generate(status_entries=status_entries))

    def post(self):
        _log.debug("MainHandler: post %s" % (self.request.body))
        self.write("MainHandler: post body: %s" % (self.request.body))


class Application(tornado.web.Application):

    def __init__(self, document_root):

        self.template_root = os.path.join(document_root,
                                          'templates')
        self.static_root = os.path.join(document_root,
                                        'static')
        uris = [
            (r"/settings", SettingsHandler),
            (r"/settings/(\w+)", SettingHandler),
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
