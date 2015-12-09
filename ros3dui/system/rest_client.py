#
# Copyright (c) 2015, Open-RnD Sp. z o.o.  All rights reserved.
#

import logging
import json
from tornado import httpclient
from ros3dui.system.util import ConfigLoader

LOG = logging.getLogger(__name__)


class DevControllerRestClient(httpclient.HTTPClient):
    """ROS3D device controller REST client"""

    API_PREFIX = "api"
    REQUEST_SNAPSHOTS = "snapshots"
    REQUEST_SNAPSHOTS_LIST = "list"

    def __init__(self):
        super(DevControllerRestClient, self).__init__()

        config = ConfigLoader()
        self.rest_url = config.get_rest_url()
        LOG.debug('rest client created')

    def _build_request_url(self, request_paths):
        """Builds request url"""
        paths = [self.rest_url, self.API_PREFIX] + request_paths
        return '/'.join(paths)

    def _process_request(self, request, method='GET'):
        """Sends request and handle the response"""
        response = self.fetch(request, method=method)

        if response.code != 200:
            LOG.error("Response status %s for request %s", response.code,
                      request)
            return None

        return response.body

    def get_snapshots_list(self):
        """Returns list of snapshots"""
        request = self._build_request_url(
            [self.REQUEST_SNAPSHOTS, self.REQUEST_SNAPSHOTS_LIST])

        return json.loads(self._process_request(request))

    def get_snapshot(self, snapshot_id):
        """Returns details of snapshot identyfied by `snapshot_id` parameter"""

        request = self._build_request_url(
            [self.REQUEST_SNAPSHOTS, snapshot_id])

        return self._process_request(request)

    def delete_snapshots(self):
        """Deletes all snapshots"""

        request = self._build_request_url(
            [self.REQUEST_SNAPSHOTS, self.REQUEST_SNAPSHOTS_LIST])

        return self._process_request(request, 'DELETE')


def get_snapshots_list():
    """Returns list of snapshots using REST client"""
    client = DevControllerRestClient()
    return client.get_snapshots_list()
