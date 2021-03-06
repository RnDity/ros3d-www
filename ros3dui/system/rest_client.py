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


def convert_to_simple_value_format(internal_json):
    """Converts internal json to simple value format.

    Internal format:
    {
    "rating": {
        "status": {
            "read": true,
            "write": true,
            "status": "software"
        },
        "type": "unicode",
        "value": ""
    },
    "parallax_near_mm": {
        "status": {
            "read": true,
            "write": true,
            "status": "software"
        },
        "type": "float",
        "value": 0.0
    },
    "camera_right_hostname": {
        "status": {
            "read": true,
            "write": true,
            "status": "software"
        },
        "type": "unicode",
        "value": "100.10.10.102"
    }

    Simple value format:
    {
        "parallax_near_mm": 0.0,
        "camera_right_hostname": "100.10.10.102"
    }
    """
    ijson = json.loads(internal_json)
    out_json = {}

    for key in ijson.keys():
        value = ijson[key]['value']

        if value == "":
            continue

        out_json[key] = value

    return out_json
