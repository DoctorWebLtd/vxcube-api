# Copyright (c) 2019 Doctor Web, Ltd.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software
# and associated documentation files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE

import logging
import warnings

import requests
from requests.compat import urljoin
from tortilla import Wrap

from vxcube_api.errors import VxCubeApiException, VxCubeApiHttpException

logger = logging.getLogger(__name__)


def _parse_version(version):
    """
    Parse the version instance and return it as a float.

    :param int or float or str version:
    :return float: version
    """
    if isinstance(version, float):
        return version
    elif isinstance(version, int):
        return float(version)
    elif isinstance(version, str):
        try:
            return float(version)
        except ValueError:
            logger.error("Version must be a valid float")
            raise VxCubeApiException("Version must be a valid float")
    else:
        raise VxCubeApiException("Version must be a valid float")


class VxCubeApiRequest(object):
    """Class for sending requests and parsing responses."""

    def __init__(self, headers=None, **kwargs):
        """
        Start a session when VxCubeApiRequest is created.

        :param headers dict or None:
        :param kwargs:
        """
        self.session = requests.session()
        self.headers = headers or {}
        self.defaults = kwargs

    def _save_data(self, response, output_file):
        logger.debug("Save response to file")

        def write_file(f):
            for chunk in response.iter_content(chunk_size=1024 * 36):
                if chunk:
                    f.write(chunk)
                    f.flush()

        if hasattr(output_file, "write"):
            write_file(output_file)
        else:
            with open(output_file, "wb") as file:
                write_file(file)

        return None

    def send_request(self, *args, **kwargs):
        """Wrap session.request.

        :param args:
        :param kwargs:
        :return requests.Response: response
        """
        try:
            logger.debug("Send response")
            return self.session.request(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            logger.debug("Session closed, retrying...")
            self.session.close()
            return self.session.request(*args, **kwargs)

    def request(self, method, url, params=None, headers=None, data=None, **kwargs):
        """
        Send request to server and parse response.

        :param str method:
        :param str url:
        :param dict params:
        :param dict headers:
        :param dict data:
        :param kwargs:
        :return bool or dict or list or str or None:
        :raise VxCubeApiHttpException
        """
        logger.debug("Start building a request")
        # If kwargs contains the output_file key, a file is expected in response
        output_file = kwargs.pop("output_file", None)
        if output_file:
            logger.debug("output_file specified, set stream")
            kwargs.setdefault("stream", True)

        # Update request header
        request_headers = dict(self.headers)
        if headers is not None:
            logger.debug("Additional headers specified, update request headers")
            request_headers.update(headers)

        # Use default request parameters
        for name, value in self.defaults.items():
            kwargs.setdefault(name, value)

        # Send request
        response = self.send_request(method, url, params=params, headers=request_headers, data=data, **kwargs)

        json_response = None
        try:
            if not output_file:
                json_response = response.json()
                logger.debug("Load JSON response")
        except ValueError:
            logger.debug("Response is not a valid JSON response")

        # If request successful
        if response.ok:
            logger.debug("Response successful")
            # Write response to file if output_file specified
            if output_file:
                self._save_data(response, output_file)
                return None
            elif json_response is not None:
                return json_response
            elif response.text:
                return response.text
            return None

        # If request failed, try getting a readable error
        logger.debug("Response failed")
        msg = "Unknown error"
        if not isinstance(json_response, dict):
            logger.debug("Unknown response format: %r", json_response)
            msg = "Unknown error"
        elif "error" in json_response:
            logger.debug("Response contains 'error' key")
            msg = json_response["error"]
        elif "message" in json_response:
            logger.debug("Response contains 'message' key")
            msg = json_response["message"]
        elif response.status_code == 400 and json_response:
            logger.debug("One or more incorrect request parameters")
            messages = []
            for key in json_response:
                info = "<UNKNOWN>"
                if isinstance(json_response[key], list):
                    info = "; ".join(str(error) for error in json_response[key])
                elif isinstance(json_response[key], str):
                    info = json_response[key]
                messages.append("[{filed}] {info}".format(filed=key, info=info))
            msg = "\t".join(messages)

        raise VxCubeApiHttpException(msg, code=response.status_code, response=json_response or response.text)


class VxCubeRawApi(Wrap):
    """Raw API for Dr.Web vxCube.

    Generate URL from chain
    Example:
        >> api = VxCubeRawApi(api_key, base_url)
        >> api.analyses(analysis_id).archive.get(output_file=output_file)
        >> GET base_url/analyses/<analysis_id>/archive and save response into output_file
    """

    def __init__(self, api_key=None, base_url="https://vxcube.drweb.com/", version=2.0):
        self._api_request = VxCubeApiRequest()
        self._version = _parse_version(version)
        self._base_url = urljoin(base_url, "api-{}/".format(self._version))

        self.api_key = api_key

        if self._version < 2.0:
            warnings.warn("API version {} is out of date".format(self._version),
                          category=DeprecationWarning, stacklevel=2)

        super(VxCubeRawApi, self).__init__(self._base_url, parent=self._api_request)

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, api_key):
        self._api_key = api_key
        self._api_request.headers.update({"Authorization": "api-key {}".format(self.api_key)})
