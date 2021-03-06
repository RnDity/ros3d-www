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

import dbus
import glib
from dbus.mainloop.glib import DBusGMainLoop
import logging

_log = logging.getLogger(__name__)


class CameraManagerError(Exception):
        pass


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

class CameraManager(object):

    CM_SERVICE_NAME = 'org.ros3d.CameraController'
    CM_SERVICE_PATH = '/org/ros3d/controller'
    CM_MANAGER_IFACE = 'org.ros3d.CameraController'
    CM_DEVICE_IFACE = 'org.ros3d.Camera'

    def __init__(self):
        self.bus = dbus.SystemBus()
        # proxy to camera controller iface
        self.cm = None

    def _connect(self):
        cmobj = self.bus.get_object(self.CM_SERVICE_NAME,
                self.CM_SERVICE_PATH)
        self.cm = dbus.Interface(cmobj, self.CM_MANAGER_IFACE)

    def _get_bus_iface(self, devpath, iface):
        """Get proxy to interface and proxy for accessing interface properties
        for bus object at path `devpath` and interface `iface`
        """
        devobj = self.bus.get_object(self.CM_SERVICE_NAME,
                                    devpath)
        dev = dbus.Interface(devobj, iface)
        return dev, PropertiesWrapper(dev)

    def _get_device(self, devpath):
        """Proxy to device interface and it's properties"""
        return self._get_bus_iface(devpath,
                                   self.CM_DEVICE_IFACE)

    def get_details(self):
        try:
            self._connect()
            assert self.cm != None

            devices = self.cm.listCameras()
            _log.debug('devices: %s', devices)
            camera_data = []
            for devpath in devices:
                _, props = self._get_device(devpath)
                _log.debug('dev id: %s', props.Id)
                _log.debug('device state: %d', props.State)
                cam = dict(name=props.Id, value=props.State)
                camera_data.append(cam)
        except dbus.exceptions.DBusException, error:
            _log.error('camera controller service unavaialble, error: %s', error)
            raise CameraManagerError('Camera Controller service unavailable')
        return camera_data

def get_camera_manager():
    """Get an instance of NetworkManagerProvider"""
    glib.threads_init()
    dbus.mainloop.glib.threads_init()
    DBusGMainLoop(set_as_default=True)
    return CameraManager()
