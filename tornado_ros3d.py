import tornado.ioloop
import tornado.web
from tornado.escape import json_encode, json_decode
import sys 
from traceback import print_exc
import dbus

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
        {'id': 0, 'name': 'testName0', 'type': 1, 'recordingmode': 1, 'fps': 1 },
        {'id': 1, 'name': 'testName1', 'type': 2, 'recordingmode': 2, 'fps': 3 },
]

cameratype = [
        {'id': 0, 'cameraid': 0, 'name': 'blackmagic1', 'matrixwidthm': 1.5, 'matrixwidthp': 1.2, 'matrixheightm': 1.8, 'matrixheightp': 1.9, 'crop': 1.66, 'type': 1, 'iso': 2},
        {'id': 1, 'cameraid': 1, 'name': 'blackmagic2', 'matrixwidthm': 1.5, 'matrixwidthp': 1.2, 'matrixheightm': 1.8, 'matrixheightp': 1.9, 'crop': 1.66, 'type': 1, 'iso': 1},
]

cameraiso = [
        {'id': 0, 'cameratypeid': 0, 'name': 'iso 100', 'value': 100},
        {'id': 1, 'cameratypeid': 1, 'name': 'iso 200', 'value': 200},
]

cameramode = [
        {'id': 0, 'cameraid': 0, 'name': '5K 2:1 5120x2560'},
        {'id': 1, 'cameraid': 1, 'name': '5K HD 16:9(4800x2700)'},
        {'id': 2, 'cameraid': 1, 'name': '4K 2:1 4096x2160'},
]

camerafps = [
        {'id': 0, 'cameratypeid': 0, 'name': '25fps', 'value': 25.0},
        {'id': 1, 'cameratypeid': 0, 'name': '25.99fps', 'value': 25.99},
        {'id': 2, 'cameratypeid': 1, 'name': '24.99fps', 'value': 24.99},
        {'id': 3, 'cameratypeid': 1, 'name': '23.99fps', 'value': 23.99},
]

servo = [
        {'id': 1, 'position': 0, 'max': 20000, 'min': 0},
        {'id': 2, 'position': 0, 'max': 30022, 'min': 0},
]

bus = 0

class SettingsHandler(tornado.web.RequestHandler):
    def get(self):
        print("SettingsHandler: %s" % json_encode(settings))
        self.write("%s" % json_encode(settings))
    def post(self):
        temp = json_decode(self.request.body)
        temp2 = {}
        for key in temp:
            print("key: %s, value: %s" % (key, temp[key]))
            settings[key] = temp[key]
            print("sett: %s" % settings[key])
            temp2[key] = settings[key]
        self.write("%s" % json_encode(temp2))            

class SettingHandler(tornado.web.RequestHandler):        
    def get(self, id):
        print("SettingHandler: %s : %s" % (id, json_encode(settings[id])))
        temp = { id : settings[id] }
        self.write("%s" % json_encode(temp))
    def post(self, id):
        temp = json_decode(self.request.body)
        settings[id] = temp[id]
        print("SettingHandler post: %s: %s" % (id, json_encode(settings[id])))
        self.write(json_encode({id : settings[id]}))

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

class DbusHandler:
    dbusH = 0
    iface = 0
    print("DbusHandler\n")
    def connect(self, service, object, interface):
        print("Connect\n")
        try:
           dbusH = dbus.SystemBus()
           remote_object = dbusH.get_object(service, object)
        except dbus.DBusException:
            print_exc()
            sys.exit(1)
        print("Connect end\n")
        self.iface = dbus.Interface(remote_object, interface)
    def getStatus(self):
        temp = self.iface.GetStatus()
        return temp
    def setRange(self, id, max, min):
        temp = self.iface.SetRange(json_encode({'id': id, 'min': min ,'max': max}))
        print(temp)
        return temp
    def setPosition(self, id, value):
        temp = self.iface.SetPosition(json_encode({'id': id, 'position': value }))
        print(temp)
        return temp
    def moveBy(self, id, value):
        #print("value: %d" % value)
        temp = self.iface.MoveBy(json_encode({'id': id, 'moveby': value }))
        print(temp)
        return temp
    def setParam(self, id, name, value):
        temp = self.iface.SetParam(json_encode({'id': id, name: value }))
        print(temp)
        return temp

class ServoHandler(tornado.web.RequestHandler):
    def get(self, id, comm):
        status = json_decode(bus.getStatus())
        if (not id) or ( id == "/"):
            print ("ServoHandler no id")
            self.write(json_encode(status))
        elif id and not comm:
            print("get: id and not comm")
            id1 = int(id.replace("/",""))
            self.write(json_encode(status[id1-1]))
        elif id and comm:
            id1 = int(id.replace("/",""))
            print("get: id and comm")
            if comm == "/range":
                self.write(json_encode({'min': status[id1-1]['min'] ,'max': status[id1-1]['max']}))
            if comm == "/getstatus":
                self.write(json_encode(status[id1-1]))
            if comm == "/position":
                self.write(json_encode({'position': status[id1-1]['position']}))
        else:
            print("Else why?? error0001: %s" % id)
    def post(self, id, comm):
        if (not id) or ( id == "/"):
            print ("post: ServoHandler no id")
            self.write(json_encode(servo))
        elif id and not comm:
            id1 = int(id.replace("/",""))
            print("post: id and not comm: %s, %s" % (id, comm))
            temp = json_decode(self.request.body)
            temp2 = {}
            for key in temp:
                servo[id1][key] = temp[key]
                temp2[key] = temp [key]
            self.write(json_encode(temp2))
        elif id and comm:
            print("post: id: %s and comm: %s" %(id, comm))
            id1 = int(id.replace("/",""))
            temp = json_decode(self.request.body)
            temp2 = {}
            if comm == "/range":
                servo[id1]['min'] = temp['min']
                servo[id1]['max'] = temp['max']
                bus.setRange(id1, temp['max'], temp['min'])
            elif comm == "/position":
                bus.setPosition(id1, temp['position'])
            elif comm == "/moveby":
                bus.moveBy(id1, temp['moveby'])
                self.write(json_encode({'status': 'OK'}))
            else:
                for key in temp:
                    servo[id1][key] = temp[key]
                    temp2[key] = temp[key]
                self.write(json_encode(temp2))
        else:
            print("Else id: %s" % id)
        

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/camera", CamerasHandler),
    (r"/camera/([0-9]+)", CameraHandler),
    (r"/settings", SettingsHandler),
    (r"/settings/(\w+)", SettingHandler),
    (r"/servo(\/[0-9]+|\/|)(\/\w+|)", ServoHandler),
])

if __name__ == "__main__":
    application.listen(80)
    bus = DbusHandler()
    bus.connect("ros3d.kontroler.Server", "/ros3d/kontroler/Object", "ros3d.kontroler.Interface")
    tornado.ioloop.IOLoop.instance().start()

