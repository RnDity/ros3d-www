Ros3D Web UI
============

Web UI for Ros3D devices. The web interface can be used to configure
some aspects of Ros3D devices such as rig assignment, control mode for
servo drivers and network setup.

The WebUI by default starts on `9900` port, this can be changed by
passing `--http-port` in command line.

Installation and dependencies
-----------------------------

To install the application run::

  python setup.py install [--root=<alternative-rootfs>]

Dependencies:

- tornado
- python-dbus

Usage
-----

To run the app locally::

  ./ros3d-ui -d ./web-data

See `--help` for more information on parameters. The location of web
root has to be passed as positional argument when running.

Network configuration
---------------------

Network configuration is applied by taking to NetworkManager over
DBus. Make sure to have NM running. There is an alternative connman
interace in `ros3dui/system/network/connman.py` however it has gone
through little testing.

