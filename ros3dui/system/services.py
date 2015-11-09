#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#

from __future__ import absolute_import

import logging
import os.path
import subprocess


_log = logging.getLogger(__name__)


class ServiceReloader(object):
    """Helper wrapper class for reloading changed services. The class
    interacts with the system via a wrapper that is normally delivered
    as part of platform integration. The class will call the helper
    script passing service names in command line as arguments. The
    script is named `ros3d-ui-service-reload`. The user of this class
    needs to call a class method `set_helpers_dir()` to configure the
    location of helper tools

    Service names are as follows:
    - servo - servo controller service
    - controller - device controller service
    - camera - camera controller service
    - platform - platform controller service

    For instance if servo and camera controllers need a reload the
    helper will be called like this::

        ros3d-ui-service-reload servo camera

    The script shall return a 0 status if services were restarted
    successfuly.

    """
    HELPER_SCRIPT = 'ros3d-ui-service-reload'
    HELPERS_DIR = None

    SERVICE_SERVO = 'servo'
    SERVICE_CONTROLLER = 'controller'
    SERVICE_CAMERA = 'camera'
    SERVICE_PLATFORM = 'platform'

    SERVICES = [
        SERVICE_SERVO,
        SERVICE_CONTROLLER,
        SERVICE_CAMERA,
        SERVICE_PLATFORM
    ]


    @classmethod
    def set_helpers_dir(cls, helpers_dir):
        if not os.path.isdir(helpers_dir):
            raise RuntimeError('helpers dir %s is not a directory' % (helpers_dir))

        cls.HELPERS_DIR = helpers_dir

    @classmethod
    def check_services(cls, services):
        """Check if services in `services` list are valid
        """
        for service in services:
            if service not in cls.SERVICES:
                raise RuntimeError('Unsupported service %s' % (service))
        return True

    @classmethod
    def reload(cls, services):
        if not cls.HELPERS_DIR:
            _log.warning('helpers directory not set')
            return False

        cls.check_services(services)

        helper_script = os.path.join(cls.HELPERS_DIR,
                                     cls.HELPER_SCRIPT)
        if not os.path.exists(helper_script):
            _log.warning('helper script %s does not exist', helper_script)
            return False

        args = [helper_script]
        for service in services:
            args.append(service)

        retcode = subprocess.call(args)
        if retcode != 0:
            _log.error('service reload failed')
            return False

        return True
