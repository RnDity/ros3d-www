import tornado.ioloop
import tornado.web
from tornado.escape import json_encode

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        print ("MainHandler: get")
        #self.write("MainHandler: get")
        self.write("%s" % ([handler.regex.pattern for handler in self.application.handlers[0][1]])) 

    def post(self):
        print ("MainHandler: post %s" % (self.request.body))
        self.write("MainHandler: post body: %s" % (self.request.body))

class CamerasHandler(tornado.web.RequestHandler):
    def get(self):
        camera = {
                'name': 'blackmagic',
                'version': '2.2',
                }
        print ("CameraHandler")
        self.write("CameraHandler: %s" % json_encode(camera))

class CameraHandler(tornado.web.RequestHandler):
    def get(self,id):
        print ("CameraHandler: get, id: %s" % id)
        self.write("CameraHandler: get, id: %s" % id)

class ServoHandler(tornado.web.RequestHandler):
    def get(self):
        print ("ServoHandler")
        self.write("ServoHandler")

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/camera", CamerasHandler),
    (r"/camera/([0-9]+)", CameraHandler),
    (r"/servo", ServoHandler),
])

if __name__ == "__main__":
    application.listen(80)
    tornado.ioloop.IOLoop.instance().start()

