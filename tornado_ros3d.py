import tornado.ioloop
import tornado.web
from tornado.escape import json_encode

settings = {
        'opacity': 90,
        'opacitymin': 50,
        'opacitymax': 100,
        'opacitystep': 10,
        'networkhostname': 'wandboard-quad.local',
        'networkmode': 'static',
        'networkip': '172.27.0.144',
        'networkmask': '255.255.255.0',
        'networkgateway': '0.0.0.0',
        'networkwifimode': 'client',
        'networkwifissid': 'wandboard',
        'networkwifisecurity': 'off',
        'networkwifikey': 'wand',
        'networkntpserverip': '11.11.11.11',
        'networkntpsynchronization': 'off',
        'language': 'polski',
}

camera = [
        {'id': 0, 'name': 'testName0'},
        {'id': 1, 'name': 'testName1'},
        {'id': 2, 'name': 'testName2'},
        {'id': 3, 'name': 'testName3'},
]

class SettingsHandler(tornado.web.RequestHandler):
    def get(self):
        print("SettingsHandler: %s" % json_encode(settings))
        self.write("%s" % json_encode(settings))

class SettingHandler(tornado.web.RequestHandler):        
    def get(self, id):
        print("SettingHandler: %s : %s" % (id, json_encode(settings[id])))
        temp = { id : settings[id] }
        self.write("%s" % json_encode(temp))

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print ("MainHandler: get")
        handlers = ([handler.regex.pattern for handler in self.application.handlers[0][1]])
        self.write ("%s" % (json_encode(handlers)))

    def post(self):
        print ("MainHandler: post %s" % (self.request.body))
        self.write("MainHandler: post body: %s" % (self.request.body))

class CamerasHandler(tornado.web.RequestHandler):
    def get(self):
        print ("CamerasHandler: %s" % json_encode(camera))
        self.write("%s" % json_encode(camera))

class CameraHandler(tornado.web.RequestHandler):
    def get(self,id):
        print camera
        print ("CameraHandler, id: %s, %s" % (id, camera[int(id)]))
        self.write("%s" % json_encode(camera[int(id)]))

class ServoHandler(tornado.web.RequestHandler):
    def get(self):
        print ("ServoHandler")
        self.write("ServoHandler")

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/camera", CamerasHandler),
    (r"/camera/([0-9]+)", CameraHandler),
    (r"/servo", ServoHandler),
    (r"/settings", SettingsHandler),
    (r"/settings/(\w+)", SettingHandler),
])

if __name__ == "__main__":
    application.listen(80)
    tornado.ioloop.IOLoop.instance().start()

