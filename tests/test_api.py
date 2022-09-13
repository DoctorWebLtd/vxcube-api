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

import datetime
import io

import mock
import pytest
from dateutil.tz import tzutc
from mock import call

from vxcube_api import VxCubeApi
from vxcube_api.api import return_objects
from vxcube_api.errors import VxCubeApiException
from vxcube_api.objects import Analysis, Sample, Task


def mock_method_for_one(self):
    return dict(id=1, test="test")


def mock_method_for_many(self):
    return [dict(id=1, test="test"), dict(id=2, test="test")]


def test_return_objects_decorator_one_obj():
    test_obj = mock.Mock()
    result = return_objects(test_obj)(mock_method_for_one)("self")

    assert isinstance(result, mock.Mock)
    test_obj.assert_called_once_with(id=1, test="test")


def test_return_objects_decorator_one_obj_with_raw_api():
    test_obj = mock.Mock()
    self = mock.Mock(_raw_api="test raw api")
    result = return_objects(test_obj, True)(mock_method_for_one)(self)

    assert isinstance(result, mock.Mock)
    test_obj.assert_called_once_with(_raw_api="test raw api", id=1, test="test")


def test_return_objects_decorator_many_obj():
    test_obj = mock.Mock()
    result = return_objects(test_obj)(mock_method_for_many)("self")

    assert isinstance(result, list)
    assert len(result) == 2
    test_obj.assert_has_calls((
        call(id=1, test="test"),
        call(id=2, test="test")
    ))


def test_return_objects_decorator_many_obj_with_raw_api():
    test_obj = mock.Mock()
    self = mock.Mock(_raw_api="test raw api")
    result = return_objects(test_obj, True)(mock_method_for_many)(self)

    assert isinstance(result, list)
    assert len(result) == 2
    test_obj.assert_has_calls((
        call(_raw_api="test raw api", id=1, test="test"),
        call(_raw_api="test raw api", id=2, test="test")
    ))


def test_return_objects_bad_value():
    test_obj = mock.Mock()
    result = return_objects(test_obj)(lambda x: None)("self")

    assert result is None
    test_obj.assert_not_called()


def test_create_vxcubeapi():
    api = VxCubeApi(api_key="test", base_url="http://test", version=2.0)
    assert api._raw_api.api_key == "test"
    assert api._raw_api._version == 2.0
    assert api._raw_api._base_url == "http://test/api-2.0/"


def test_vxcubeapi_login():
    request = mock.Mock(return_value={"api_key": "test"})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        api.login("login", "password")

    assert api._raw_api.api_key == "test"
    request.assert_called_with(method="post", url="http://test/api-2.0/login",
                               params={}, headers={}, json={"login": "login", "password": "password", "new_key": False})


def test_vxcubeapi_login_with_new_key():
    request = mock.Mock(return_value={"api_key": "test"})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        api.login("login", "password", new_key=True)

    assert api._raw_api.api_key == "test"
    request.assert_called_with(method="post", url="http://test/api-2.0/login",
                               params={}, headers={}, json={"login": "login", "password": "password", "new_key": True})


def test_vxcubeapi_login_bad_response():
    request = mock.Mock(return_value=("bad"))
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        with pytest.raises(VxCubeApiException):
            api.login("login", "password")

    request.assert_called_with(method="post", url="http://test/api-2.0/login",
                               params={}, headers={}, json={"login": "login", "password": "password", "new_key": False})


def test_vxuserapi_sessions():
    request = mock.Mock(return_value=[{"api_key": "test-api-key", "start_date": "2018-04-08T15:16:23.420000+00:00"}])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        sessions = api.sessions()

        assert len(sessions) == 1
        assert sessions[0].api_key == "test-api-key"
        assert sessions[0].start_date == datetime.datetime(2018, 4, 8, 15, 16, 23, 420000, tzinfo=tzutc())

    request.assert_called_with(method="get", url="http://test/api-2.0/sessions",
                               params={}, headers={})


def test_vxuserapi_platforms():
    request = mock.Mock(return_value=[{"code": "test_code", "name": "test_name", "os_code": "test_os"}])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        platforms = api.platforms()

        assert len(platforms) == 1
        assert platforms[0].code == "test_code"
        assert platforms[0].name == "test_name"
        assert platforms[0].os_code == "test_os"

    request.assert_called_with(method="get", url="http://test/api-2.0/platforms",
                               params={}, headers={})


def test_vxuserapi_formats():
    request = mock.Mock(return_value=[{"name": "test_name", "group_name": "test_group", "platforms": ["test_pl"]}])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        formats = api.formats()

        assert len(formats) == 1
        assert formats[0].name == "test_name"
        assert formats[0].group_name == "test_group"
        assert formats[0].platforms == ["test_pl"]

    request.assert_called_with(method="get", url="http://test/api-2.0/formats",
                               params={}, headers={})


def test_vxuserapi_license():
    test_license = {
        "start_date": "2018-04-08T15:16:23.420000+00:00",
        "end_date": "2019-04-08T15:16:23.420000+00:00",
        "uploads_spent": 0,
        "uploads_total": 10,
        "vnc_allowed": True,
        "cureit_allowed": False,
        "upload_max_size": 1024,
        "max_run_time": 600
    }
    request = mock.Mock(return_value=test_license)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        api_license = api.license()

        assert api_license.start_date == datetime.datetime(2018, 4, 8, 15, 16, 23, 420000, tzinfo=tzutc())
        assert api_license.end_date == datetime.datetime(2019, 4, 8, 15, 16, 23, 420000, tzinfo=tzutc())
        assert api_license.uploads_spent == 0
        assert api_license.uploads_total == 10
        assert api_license.vnc_allowed is True
        assert api_license.cureit_allowed is False
        assert api_license.upload_max_size == 1024
        assert api_license.max_run_time == 600

    request.assert_called_with(method="get", url="http://test/api-2.0/license",
                               params={}, headers={})


def test_vxuserapi_one_sample():
    request = mock.Mock(return_value={"id": 42})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        sample = api.samples(sample_id=42)

        assert isinstance(sample, Sample)
        assert sample.id == 42
        assert sample._raw_api is api._raw_api

    request.assert_called_with(method="get", url="http://test/api-2.0/samples/42",
                               params={}, headers={})


def test_vxuserapi_many_samples():
    kwargs = dict(
        count=4,
        offset=2,
        md5=None,
        sha1="sha1",
        sha256=None,
        format_name=None,
        format_group_name=None
    )
    request = mock.Mock(return_value=[{"id": 23}, {"id": 42}])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        samples = api.samples(**kwargs)

        assert isinstance(samples, list)
        assert len(samples) == 2
        assert samples[0].id == 23
        assert samples[0]._raw_api is api._raw_api
        assert samples[1].id == 42
        assert samples[1]._raw_api is api._raw_api

    request.assert_called_with(method="get", url="http://test/api-2.0/samples",
                               params={}, headers={}, json={"count": 4, "offset": 2, "sha1": "sha1"})


def test_vxuserapi_samples_iter():
    kwargs = dict(
        count=4,
        offset=2,
        md5=None,
        sha1="sha1",
        sha256=None,
        format_name=None,
        format_group_name=None
    )
    request = mock.Mock(return_value=[{"id": 23}, {"id": 42}])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        samples = list(api.samples_iter(**kwargs))

        assert isinstance(samples, list)
        assert len(samples) == 2
        assert samples[0].id == 23
        assert samples[0]._raw_api is api._raw_api
        assert samples[1].id == 42
        assert samples[1]._raw_api is api._raw_api

    request.assert_called_with(method="get", url="http://test/api-2.0/samples",
                               params={}, headers={}, json={"count": 100, "offset": 2, "sha1": "sha1"})


def test_upload_sample():
    request = mock.Mock(return_value={"id": 23})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        file = io.BytesIO(b"test_data")
        file.name = "test.name"
        sample = api.upload_sample(file)
        assert sample.id == 23
        assert sample._raw_api is api._raw_api


def test_upload_samples():
    request = mock.Mock(return_value={"samples": [{"id": 23}, {"id": 27}]})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        file = io.BytesIO(b"zip_test_data")
        file.name = "test.zip"
        samples = api.upload_samples(file)
        assert isinstance(samples, list)
        assert len(samples) == 2
        assert samples[0].id == 23
        assert samples[0]._raw_api is api._raw_api
        assert samples[1].id == 27
        assert samples[1]._raw_api is api._raw_api


def test_vxuserapi_one_analysis():
    request = mock.Mock(return_value={"id": 42})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        analysis = api.analyses(analysis_id=42)

        assert isinstance(analysis, Analysis)
        assert analysis.id == 42
        assert analysis._raw_api is api._raw_api

    request.assert_called_with(method="get", url="http://test/api-2.0/analyses/42",
                               params={}, headers={})


def test_vxuserapi_many_analyses():
    kwargs = dict(
        count=4,
        offset=2,
        format_group_name=None
    )
    request = mock.Mock(return_value=[{"id": 23}, {"id": 42}])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        analyses = api.analyses(**kwargs)

        assert isinstance(analyses, list)
        assert len(analyses) == 2
        assert analyses[0].id == 23
        assert analyses[0]._raw_api is api._raw_api
        assert analyses[1].id == 42
        assert analyses[1]._raw_api is api._raw_api

    request.assert_called_with(method="get", url="http://test/api-2.0/analyses",
                               params={}, headers={}, json={"count": 4, "offset": 2})


def test_vxuserapi_analyses_iter():
    kwargs = dict(
        count=4,
        offset=2,
        format_group_name=None
    )
    request = mock.Mock(return_value=[{"id": 23}, {"id": 42}])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        analyses = list(api.analyses_iter(**kwargs))

        assert isinstance(analyses, list)
        assert len(analyses) == 2
        assert analyses[0].id == 23
        assert analyses[0]._raw_api is api._raw_api
        assert analyses[1].id == 42
        assert analyses[1]._raw_api is api._raw_api

    request.assert_called_with(method="get", url="http://test/api-2.0/analyses",
                               params={}, headers={}, json={"count": 100, "offset": 2})


def test_start_analysis():
    kwargs = dict(
        sample_id=23,
        platforms=["p1", "p2"],
        analysis_time=30,
        format_name=None,
        custom_cmd=None,
    )
    request = mock.Mock(return_value={"id": 42})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        analysis = api.start_analysis(**kwargs)

        assert isinstance(analysis, Analysis)
        assert analysis.id == 42
        assert analysis._raw_api is api._raw_api

    request.assert_called_with(method="post", url="http://test/api-2.0/analyses", params={}, headers={},
                               json={"sample_id": 23, "platforms": ["p1", "p2"], "analysis_time": 30, "copylog": False,
                                     "crypto_api_limit": 64, "dump_size_limit": 64, "flex_time": False,
                                     "get_lib": False, "injects_limit": 100, "dump_browsers": True,
                                     "dump_mapped": True, "dump_ssdt": True, "dump_processes": True, "no_clean": False,
                                     "write_file_limit": 512})


def test_get_task():
    request = mock.Mock(return_value={"id": 42})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        api = VxCubeApi(base_url="http://test", version=2.0)
        task = api.task(42)

        assert isinstance(task, Task)
        assert task.id == 42
        assert task._raw_api is api._raw_api

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42",
                               params={}, headers={})
