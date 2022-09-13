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

import mock
import pytest
import requests

from vxcube_api.errors import VxCubeApiException
from vxcube_api.raw_api import VxCubeApiRequest, VxCubeRawApi, _parse_version


@pytest.mark.parametrize("version, result", [
    (1.0, 1.0),
    (1, 1.0),
    ("1.0", 1.0),
    ("2", 2.0),
    (1.4, 1.4),
    ("2.1", 2.1),
])
def test_parse_version(version, result):
    assert _parse_version(version) == result


@pytest.mark.parametrize("version", [
    "BadValue",
    [42],
    {42},
])
def test_parse_version_bad_value(version):
    with pytest.raises(VxCubeApiException):
        _parse_version(version)


def test_raw_api_empty():
    raw_api = VxCubeRawApi(base_url="http://test", version=23.42)

    assert isinstance(raw_api._api_request, VxCubeApiRequest)
    assert raw_api._version == 23.42
    assert raw_api._base_url == "http://test/api-23.42/"
    assert raw_api._api_key is None
    assert raw_api.api_key is None


def test_raw_api_deprecation_warning():
    with pytest.deprecated_call():
        VxCubeRawApi(base_url="http://test", version=1.0)


def test_init_with_api_key():
    raw_api = VxCubeRawApi(api_key="test_key")

    assert raw_api.api_key == "test_key"
    assert "Authorization" in raw_api._api_request.headers
    assert raw_api._api_request.headers["Authorization"] == "api-key test_key"


def test_set_api_key():
    raw_api = VxCubeRawApi()
    raw_api.api_key = "test_key"

    assert raw_api.api_key == "test_key"
    assert "Authorization" in raw_api._api_request.headers
    assert raw_api._api_request.headers["Authorization"] == "api-key test_key"


def test_set_empty_api_key():
    raw_api = VxCubeRawApi()
    raw_api.api_key = "test_key"

    assert raw_api.api_key == "test_key"
    assert "Authorization" in raw_api._api_request.headers
    assert raw_api._api_request.headers["Authorization"] == "api-key test_key"

    raw_api.api_key = None
    assert raw_api.api_key is None
    assert "Authorization" in raw_api._api_request.headers
    assert raw_api._api_request.headers["Authorization"] == "api-key None"


def test_api_request():
    api_request = VxCubeApiRequest()
    assert isinstance(api_request.session, requests.Session)
    assert api_request.headers == {}
    assert api_request.defaults == {}


def test_api_request_send_request():
    api_request = VxCubeApiRequest()
    request = mock.Mock()
    api_request.session.request = request
    api_request.send_request("test_arg", test_kwarg="test_kwarg")
    assert request.assert_called_with("test_arg", test_kwarg="test_kwarg") is None


def test_api_request_send_request_with_connection_error():
    session = mock.Mock(**{"request.side_effect": requests.exceptions.ConnectionError})
    session.close = mock.Mock()
    session.request = mock.Mock(side_effect=(requests.exceptions.ConnectionError, "test_response"))

    api_request = VxCubeApiRequest()
    api_request.session = session
    response = api_request.send_request("test_arg", test_kwarg="test_kwarg")

    assert session.close.assert_called_once() is None
    assert response == "test_response"


def test_api_request_basic_json():
    api_request = VxCubeApiRequest()
    dct = {"test_key": "test_value"}
    response = mock.Mock(**{"ok": True, "json.return_value": dct})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request
    rs = api_request.request("GET", "http://test.url")

    assert rs is dct
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, headers={}, data=None)


def test_api_request_not_json_content():
    api_request = VxCubeApiRequest()
    text = "test_text"
    response = mock.Mock(**{"ok": True, "json.side_effect": ValueError, "text": text})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request
    rs = api_request.request("GET", "http://test.url")

    assert rs is text
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, headers={}, data=None)


def test_api_request_not_json_content_and_empty_body():
    api_request = VxCubeApiRequest()
    response = mock.Mock(**{"ok": True, "json.side_effect": ValueError, "text": ""})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request
    rs = api_request.request("GET", "http://test.url")

    assert rs is None
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, headers={}, data=None)


def test_api_request_error_without_json():
    api_request = VxCubeApiRequest()
    response = mock.Mock(**{"ok": False, "json.side_effect": ValueError, "text": ""})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request

    with pytest.raises(VxCubeApiException, match="Unknown error"):
        api_request.request("GET", "http://test.url")
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, headers={}, data=None)


def test_api_request_error_json_error():
    api_request = VxCubeApiRequest()
    dct = {"error": "test_message"}
    response = mock.Mock(**{"ok": False, "json.return_value": dct})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request

    with pytest.raises(VxCubeApiException, match="test_message"):
        api_request.request("GET", "http://test.url")
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, headers={}, data=None)


def test_api_request_error_json_message():
    api_request = VxCubeApiRequest()
    dct = {"message": "test_message"}
    response = mock.Mock(**{"ok": False, "json.return_value": dct})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request

    with pytest.raises(VxCubeApiException, match="test_message"):
        api_request.request("GET", "http://test.url")
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, headers={}, data=None)


def test_api_request_error_request_parameters():
    api_request = VxCubeApiRequest()
    dct = {"k1": "v1", "k2": ["v1", "v2"], "k3": {"bad": "value"}}
    response = mock.Mock(**{"ok": False, "json.return_value": dct, "status_code": 400})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request

    with pytest.raises(VxCubeApiException) as exc_info:
        api_request.request("GET", "http://test.url")

    assert "[k1] v1" in str(exc_info.value)
    assert "[k2] v1; v2" in str(exc_info.value)
    assert "[k3] <UNKNOWN>" in str(exc_info.value)
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, headers={}, data=None)


def test_api_request_output_file_as_file():
    api_request = VxCubeApiRequest()
    response = mock.Mock(**{"ok": True, "iter_content.return_value": [b"test_file_content"]})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request
    output_file = mock.Mock()
    rs = api_request.request("GET", "http://test.url", output_file=output_file)

    assert rs is None
    output_file.write.assert_called_with(b"test_file_content")
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, headers={}, data=None, stream=True)


def test_api_request_output_file_as_str():
    api_request = VxCubeApiRequest()
    response = mock.Mock(**{"ok": True, "iter_content.return_value": [b"test_file_content"]})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request

    file = mock.mock_open()
    with mock.patch("vxcube_api.raw_api.open", file):
        rs = api_request.request("GET", "http://test.url", output_file="test_file")

    assert rs is None
    file.assert_called_with("test_file", "wb")
    file().write.assert_called_with(b"test_file_content")
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, headers={}, data=None, stream=True)


def test_api_request_default_headers():
    api_request = VxCubeApiRequest(headers={"default": "value"})
    dct = {"test_key": "test_value"}
    response = mock.Mock(**{"ok": True, "json.return_value": dct})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request
    rs = api_request.request("GET", "http://test.url", headers={"request": "value"})

    assert rs is dct
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, data=None,
                                    headers={"request": "value", "default": "value"})


def test_api_request_default_headers_save_value():
    api_request = VxCubeApiRequest(headers={"default": "value1"})
    dct = {"test_key": "test_value"}
    response = mock.Mock(**{"ok": True, "json.return_value": dct})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request
    rs = api_request.request("GET", "http://test.url", headers={"default": "value2"})

    assert rs is dct
    assert api_request.headers == {"default": "value1"}
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, data=None,
                                    headers={"default": "value2"})


def test_api_request_default_parameters():
    api_request = VxCubeApiRequest(default="value")
    dct = {"test_key": "test_value"}
    response = mock.Mock(**{"ok": True, "json.return_value": dct})
    send_request = mock.Mock(return_value=response)
    api_request.send_request = send_request
    rs = api_request.request("GET", "http://test.url", headers={"default": "value2"})

    assert rs is dct
    send_request.assert_called_once()
    send_request.assert_called_with("GET", "http://test.url", params=None, data=None,
                                    headers={"default": "value2"}, default="value")
