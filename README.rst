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

Platform integration
--------------------

Once the configuration is applied, some services may need to be
reloaded/restarted. The app will look for and run
`ros3d-ui-service-reload` script passing the names of affected
services (`servo`, `controller`, `camera`, `platform`) as command line
arguments. The actual service names in the system or the required
sequence of operations may differ depending on the system, hence an
integrator is expected to provide and deploy a script that will
perform the necessary action. For instance, if the device controller
is managed by `systemd` and named `ros3d-controller`, the reload
script may look like this::

  #!/bin/sh

  restart_service() {
      local service

      case $1 in
          controller)
              service=ros3d-controller
              ;;
          # other cases ..
      esac

      if [ -n "$service" ]; then
          systemctl restart $service || echo "-- Failed to restart $service"
      fi
  }

  for s in $*; do
      restart_service $s
  done


