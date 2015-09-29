#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#
"""Utility classes for Ros3D"""

import logging
import ConfigParser
import os.path
import os

class ConfigLoader(object):
    """Ros3D system configuration loader"""

    DEFAULT_PATH = '/etc/ros3d.conf'
    CONFIG_PATH = DEFAULT_PATH

    logger = logging.getLogger(__name__)

    def __init__(self, path=None):
        self.config = None
        self._load_config(path if path else ConfigLoader.CONFIG_PATH)

    def _load_config(self, path):
        """Load configuration from file given by `path`"""
        self.config = ConfigParser.ConfigParser()

        loaded = self.config.read(path)
        if not loaded:
            self.logger.error('failed to load configuration from %s',
                              path)

    def _get(self, section, name, default=None):
        """Try to get an option from configuration. If option is not found,
        return `default`"""
        try:
            return self.config.get(section, name)
        except ConfigParser.Error:
            self.logger.exception('failed to load %s:%s, returning default %r',
                                  section, name, default)
            return default

    def get_system(self):
        """Get assigned system"""
        sys_name = self._get('common', 'system', '')
        return sys_name

    def set_system(self, value):
        if not self.config.has_section('common'):
            self.config.add_section('common')
        self.config.set('common', 'system', value)

    def get_aladin(self):
        """Get Aladin control mode"""
        return self._get('common', 'aladin', '')

    def set_aladin(self, value):
        if not self.config.has_section('common'):
            self.config.add_section('common')
        self.config.set('common', 'aladin', value)

    def write(self):
        import tempfile
        import shutil

        fd, path = tempfile.mkstemp()
        self.logger.debug('writing config to temp file: %s', path)
        with os.fdopen(fd, 'w') as outf:
            self.config.write(outf)

        self.logger.debug('replacing %s', ConfigLoader.CONFIG_PATH)
        shutil.move(path, ConfigLoader.CONFIG_PATH)

    @classmethod
    def set_config_location(cls, path):
        cls.logger.debug('setting config path to %s', path)
        cls.CONFIG_PATH = path
