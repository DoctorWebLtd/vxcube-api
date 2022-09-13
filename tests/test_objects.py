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

import mock
import pytest
from dateutil.tz import tzutc
from websocket import WebSocketConnectionClosedException

from vxcube_api.errors import VxCubeApiException
from vxcube_api.objects import (Analysis, ApiObject, CureIt, Sample, Session,
                                Task)
from vxcube_api.raw_api import VxCubeRawApi


def test_api_object():
    class ApiTestObj(ApiObject):
        __slots__ = ("attr1", "attr2", "attr3")
        _time_fields = ("attr2", "attr3")

    values = dict(
        _raw_api="value_raw_api",
        attr1="value_attr1",
        attr2="2018-04-08T15:16:23.420000+00:00",
        attr3=None,
        attr4="value_attr3"
    )
    obj = ApiTestObj(**values)

    assert obj._raw_api is values["_raw_api"]
    assert obj.attr1 is values["attr1"]
    assert obj.attr2 == datetime.datetime(2018, 4, 8, 15, 16, 23, 420000, tzinfo=tzutc())
    assert obj.attr3 is None
    with pytest.raises(AttributeError):
        getattr(obj, "attr4")


def test_sessions():
    values = dict(
        api_key="{}-{}-{}-{}-{}".format("a" * 8, "b" * 4, "c" * 4, "d" * 4, "e" * 12),
        start_date="2018-04-08T15:16:23.420000+00:00"
    )
    session = Session(**values)

    assert session.api_key == "{}-{}-{}-{}-{}".format("a" * 8, "b" * 4, "c" * 4, "d" * 4, "e" * 12)
    assert session.start_date == datetime.datetime(2018, 4, 8, 15, 16, 23, 420000, tzinfo=tzutc())


def test_delete_session():
    values = dict(
        api_key="{}-{}-{}-{}-{}".format("a" * 8, "b" * 4, "c" * 4, "d" * 4, "e" * 12),
        start_date="2018-04-08T15:16:23.420000+00:00"
    )

    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        session = Session(_raw_api=raw_api, **values)
        assert session.delete()

    request.assert_called_with(method="delete", url="http://test/api-2.0/sessions/{}".format(values["api_key"]),
                               params={}, headers={})


def test_sample():
    values = dict(
        id=1,
        name="sample",
        size=2342,
        format_name="exe",
        upload_date="2018-04-08T15:16:23.420000+00:00",
        md5="md5hash",
        sha1="sha1hash",
        sha256="sha256hash",
        is_x64=True,
        platforms=["win7x64", "win10x64_1511"],
    )
    sample = Sample(**values)
    assert sample.id == 1
    assert sample.name == "sample"
    assert sample.size == 2342
    assert sample.format_name == "exe"
    assert sample.upload_date == datetime.datetime(2018, 4, 8, 15, 16, 23, 420000, tzinfo=tzutc())
    assert sample.md5 == "md5hash"
    assert sample.sha1 == "sha1hash"
    assert sample.sha256 == "sha256hash"
    assert sample.is_x64 is True
    assert sample.platforms == ["win7x64", "win10x64_1511"]

    with pytest.raises(VxCubeApiException):
        sample._api()

    with pytest.raises(VxCubeApiException):
        sample.download("tmp")


@pytest.mark.parametrize(
    "analysis_id, task_id, _type", [(1, None, "Analysis"), (None, 2, "Task")]
)
def test_cureit(analysis_id, task_id, _type):
    values = dict(
        status="successful",
        retries=None,
        analysis_id=analysis_id,
        task_id=task_id,
    )
    cureit = CureIt(**values)

    assert cureit.status == "successful"
    assert cureit.retries is None
    assert cureit.analysis_id == analysis_id
    assert cureit.task_id == task_id

    assert "CureIt ({type}[{id}]) status: {status}".format(type=_type, id=cureit.analysis_id or cureit.task_id,
                                                           status=cureit.status) == str(cureit)


def test_cureit_without_bound():
    values = dict(
        status="successful",
        retries=None,
    )
    with pytest.raises(VxCubeApiException):
        CureIt(**values)


@pytest.mark.parametrize("status, state", [
    ("successful",
     dict(is_success=True, is_failed=False, is_deleted=False, is_finished=True, is_processing=False,
          is_small_file=False)),
    ("failed",
     dict(is_success=False, is_failed=True, is_deleted=False, is_finished=True, is_processing=False,
          is_small_file=False)),
    ("deleted",
     dict(is_success=False, is_failed=False, is_deleted=True, is_finished=True, is_processing=False,
          is_small_file=False)),
    ("processing",
     dict(is_success=False, is_failed=False, is_deleted=False, is_finished=False, is_processing=True,
          is_small_file=False)),
    ("small_file",
     dict(is_success=False, is_failed=False, is_deleted=False, is_finished=True, is_processing=False,
          is_small_file=True)),
])
def test_cureit_status(status, state):
    values = dict(
        status=status,
        retries=None,
        analysis_id=1,
    )
    cureit = CureIt(**values)

    for attr in state:
        assert getattr(cureit, attr) == state[attr]


@pytest.mark.parametrize("status, retries, result", [
    ("successful", None, False),
    ("failed", None, True),
    ("deleted", None, True),
    ("processing", None, False),
    ("small_file", None, False),
    ("failed", {"left": 2}, True),
    ("deleted", {"left": 2}, True),
    ("failed", {"left": 0, "after": "2018-04-08T15:16:23.420000+00:00"}, False),
])
def test_cureit_can_retrying(status, retries, result):
    values = dict(
        status=status,
        retries=retries,
        analysis_id=1,
    )
    cureit = CureIt(**values)
    assert cureit.can_retrying == result


def test_task():
    values = dict(
        # base
        id=1,
        status="successful",
        platform_code="winxpx86",
        start_date="2018-04-08T15:16:23.420000+00:00",
        end_date="2018-04-08T15:16:23.420000+00:00",
        maliciousness=3,

        # processing
        message="test_message",
        progress=99,

        # finished
        verdict="guilty",
        rules={"neutral": ["Hugo wins the lottery"]},
    )
    task = Task(**values)
    assert task.id == 1
    assert task.status == "successful"
    assert task.platform_code == "winxpx86"
    assert task.start_date == datetime.datetime(2018, 4, 8, 15, 16, 23, 420000, tzinfo=tzutc())
    assert task.end_date == datetime.datetime(2018, 4, 8, 15, 16, 23, 420000, tzinfo=tzutc())
    assert task.maliciousness == 3

    assert task.message == "test_message"
    assert task.progress == 99

    assert task.verdict == "guilty"
    assert task.rules == {"neutral": ["Hugo wins the lottery"]}


@pytest.mark.parametrize("status, state", [
    ("successful",
     dict(is_success=True, is_failed=False, is_deleted=False, is_finished=True, is_processing=False)),
    ("failed",
     dict(is_success=False, is_failed=True, is_deleted=False, is_finished=True, is_processing=False)),
    ("deleted",
     dict(is_success=False, is_failed=False, is_deleted=True, is_finished=True, is_processing=False)),
    ("processing",
     dict(is_success=False, is_failed=False, is_deleted=False, is_finished=False, is_processing=True)),
    ("in queue",
     dict(is_success=False, is_failed=False, is_deleted=False, is_finished=False, is_processing=True)),
])
def test_task_status(status, state):
    task = Task(status=status)
    for attr in state:
        assert getattr(task, attr) == state[attr]


def test_task_is_android():
    task = Task(platform_code="winxpx86")
    assert not task.is_android

    task = Task(platform_code="android4.3")
    assert task.is_android

    task = Task(platform_code="android7.1")
    assert task.is_android


def test_analysis():
    values = dict(
        id=1,
        sha1="sha1hash",
        sample_id=1,
        size=2342,
        format_name="exe",
        start_date="2018-04-08T15:16:23.420000+00:00",
        user_name="test_user",
        tasks=[dict(
            id=1,
        )],
    )
    analysis = Analysis(**values)

    assert analysis.id == 1
    assert analysis.sha1 == "sha1hash"
    assert analysis.sample_id == 1
    assert analysis.size == 2342
    assert analysis.format_name == "exe"
    assert analysis.start_date == datetime.datetime(2018, 4, 8, 15, 16, 23, 420000, tzinfo=tzutc())
    assert analysis.user_name == "test_user"
    assert isinstance(analysis.tasks, list)
    assert isinstance(analysis.tasks[0], Task)
    assert analysis.tasks[0].id == 1


def test_analysis_progress():
    values = dict(
        tasks=[dict(
            id=1,
            status="in queue",
            progress=0
        ), dict(
            id=2,
            status="processing",
            progress=35
        ), dict(
            id=3,
            status="failed",
        ), dict(
            id=4,
            status="processing",
            progress=65
        )],
    )
    analysis = Analysis(**values)
    assert analysis.is_processing
    assert not analysis.is_finished
    assert analysis.total_progress == 50  # (0 + 35 + 100 + 65) / 4


def test_sample_download():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        sample = Sample(id=42, _raw_api=raw_api)
        sample.download(output_file="test_output")

    request.assert_called_with(method="get", url="http://test/api-2.0/samples/42/download",
                               params={}, headers={}, output_file="test_output")


def test_cureit_download_by_analysis():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        cureit = CureIt(analysis_id=42, _raw_api=raw_api)
        cureit.download(output_file="test_output")

    request.assert_called_with(method="get", url="http://test/api-2.0/analyses/42/cureit.exe",
                               params={}, headers={}, output_file="test_output")


def test_cureit_retry_by_analysis():
    request = mock.Mock(return_value={"status": "processing"})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        cureit = CureIt(analysis_id=42, status="failed", _raw_api=raw_api)

        assert cureit.retry()
        assert cureit.analysis_id == 42
        assert cureit.status == "processing"
        assert cureit._raw_api is raw_api

    request.assert_called_with(method="put", url="http://test/api-2.0/analyses/42/cureit",
                               params={}, headers={})


def test_cureit_download_by_task():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        cureit = CureIt(task_id=42, _raw_api=raw_api)
        cureit.download(output_file="test_output")

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/cureit.exe",
                               params={}, headers={}, output_file="test_output")


def test_cureit_retry_by_task():
    request = mock.Mock(return_value={"status": "processing"})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        cureit = CureIt(task_id=42, status="failed", _raw_api=raw_api)

        assert cureit.retry()
        assert cureit.task_id == 42
        assert cureit.status == "processing"
        assert cureit._raw_api is raw_api

    request.assert_called_with(method="put", url="http://test/api-2.0/tasks/42/cureit",
                               params={}, headers={})


def test_task_windows_cureit():
    request = mock.Mock(return_value={"status": "processing", "retries": None})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, platform_code="winxpx86", _raw_api=raw_api)
        cureit = task.cureit()

        assert cureit.task_id == 42
        assert cureit.status == "processing"
        assert cureit.retries is None
        assert cureit._raw_api is raw_api

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/cureit",
                               params={}, headers={})


def test_task_android_cureit():
    request = mock.Mock(return_value={"status": "processing", "retries": None})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, platform_code="android4.3", _raw_api=raw_api)
        cureit = task.cureit()

        assert cureit is None

    request.assert_not_called()


def test_task_dumps():
    request = mock.Mock(return_value=["dump23", "dump42"])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        dumps = task.dumps(23, 42, "lost")

        assert len(dumps) == 2
        assert dumps[0] == "dump23"
        assert dumps[1] == "dump42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/dumps",
                               params={}, headers={}, json={"count": 23, "offset": 42, "search": "lost"})


def test_task_dumps_iter():
    request = mock.Mock(return_value={"total_count": 2, "items": ["dump23", "dump42"]})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        dumps = list(task.dumps_iter(count_per_request=23, search="lost"))

        assert len(dumps) == 2
        assert dumps[0] == "dump23"
        assert dumps[1] == "dump42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/dumps",
                               params={}, headers={}, json={"count": 23, "offset": 0, "search": "lost"})


def test_task_drops():
    request = mock.Mock(return_value=["file23", "file42"])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        files = task.drops(23, 42, "lost")

        assert len(files) == 2
        assert files[0] == "file23"
        assert files[1] == "file42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/drops",
                               params={}, headers={}, json={"count": 23, "offset": 42, "search": "lost"})


def test_task_drops_iter():
    request = mock.Mock(return_value={"total_count": 2, "items": ["file23", "file42"]})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        files = list(task.drops_iter(count_per_request=23, search="lost"))

        assert len(files) == 2
        assert files[0] == "file23"
        assert files[1] == "file42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/drops",
                               params={}, headers={}, json={"count": 23, "offset": 0, "search": "lost"})


def test_task_networks():
    request = mock.Mock(return_value=["network23", "network42"])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        networks = task.networks(23, 42, "lost")

        assert len(networks) == 2
        assert networks[0] == "network23"
        assert networks[1] == "network42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/networks",
                               params={}, headers={}, json={"count": 23, "offset": 42, "search": "lost"})


def test_task_networks_iter():
    request = mock.Mock(return_value={"total_count": 2, "items": ["network23", "network42"]})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        networks = list(task.networks_iter(count_per_request=23, search="lost"))

        assert len(networks) == 2
        assert networks[0] == "network23"
        assert networks[1] == "network42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/networks",
                               params={}, headers={}, json={"count": 23, "offset": 0, "search": "lost"})


def test_task_apilog():
    request = mock.Mock(return_value=["event23", "event42"])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        apilog = task.apilog(23, 42, "lost")

        assert len(apilog) == 2
        assert apilog[0] == "event23"
        assert apilog[1] == "event42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/api_log",
                               params={}, headers={}, json={"count": 23, "offset": 42, "search": "lost"})


def test_task_apilog_iter():
    request = mock.Mock(return_value={"total_count": 2, "items": ["event23", "event42"]})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        apilog = list(task.apilog_iter(count_per_request=23, search="lost"))

        assert len(apilog) == 2
        assert apilog[0] == "event23"
        assert apilog[1] == "event42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/api_log",
                               params={}, headers={}, json={"count": 23, "offset": 0, "search": "lost"})


def test_task_intents():
    request = mock.Mock(return_value=["intent23", "intent42"])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        intents = task.intents(23, 42, "lost")

        assert len(intents) == 2
        assert intents[0] == "intent23"
        assert intents[1] == "intent42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/intents",
                               params={}, headers={}, json={"count": 23, "offset": 42, "search": "lost"})


def test_task_intents_iter():
    request = mock.Mock(return_value={"total_count": 2, "items": ["intent23", "intent42"]})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        intents = list(task.intents_iter(count_per_request=23, search="lost"))

        assert len(intents) == 2
        assert intents[0] == "intent23"
        assert intents[1] == "intent42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/intents",
                               params={}, headers={}, json={"count": 23, "offset": 0, "search": "lost"})


def test_task_phone_actions():
    request = mock.Mock(return_value=["phone_action23", "phone_action42"])
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        phone_actions = task.phone_actions(23, 42, "lost")

        assert len(phone_actions) == 2
        assert phone_actions[0] == "phone_action23"
        assert phone_actions[1] == "phone_action42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/phone_actions",
                               params={}, headers={}, json={"count": 23, "offset": 42, "search": "lost"})


def test_task_phone_actions_iter():
    request = mock.Mock(return_value={"total_count": 2, "items": ["phone_action23", "phone_action42"]})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        phone_actions = list(task.phone_actions_iter(count_per_request=23, search="lost"))

        assert len(phone_actions) == 2
        assert phone_actions[0] == "phone_action23"
        assert phone_actions[1] == "phone_action42"

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/phone_actions",
                               params={}, headers={}, json={"count": 23, "offset": 0, "search": "lost"})


def test_task_restart():
    request = mock.Mock(return_value={"status": "processing"})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, status="deleted", _raw_api=raw_api)
        assert task.restart()
        assert task.status == "processing"

    request.assert_called_with(method="post", url="http://test/api-2.0/tasks/42/restart",
                               params={}, headers={})


def test_task_restart_processing_task():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, status="processing", _raw_api=raw_api)
        assert not task.restart()

    request.assert_not_called()


def test_task_download_archive():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        task.download_archive(output_file="test_output")

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/archive",
                               params={}, headers={}, output_file="test_output")


def test_task_download_sample():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        task.download_sample(output_file="test_output")

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/sample",
                               params={}, headers={}, output_file="test_output")


def test_task_download_report():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        task.download_report(output_file="test_output")

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/report",
                               params={}, headers={}, output_file="test_output")


def test_task_storage_list():
    return_storage = {"files": [], "folders": []}
    request = mock.Mock(return_value=return_storage)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        storage = task.storage_lists()
        assert storage is return_storage

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/archive_storage",
                               params={}, headers={})


def test_task_download_from_storage():
    return_storage = {"files": [], "folders": []}
    request = mock.Mock(return_value=return_storage)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        task = Task(id=42, _raw_api=raw_api)
        task.download_storage_file(path="test_path", output_file="test_output")

    request.assert_called_with(method="get", url="http://test/api-2.0/tasks/42/archive_storage",
                               params={}, headers={}, json={"path": "test_path"}, output_file="test_output")


def test_analysis_restart():
    request = mock.Mock(return_value={"tasks": [{"id": 23, "status": "processing"}]})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        analysis = Analysis(id=42, tasks=[{"id": 23, "status": "failed"}], _raw_api=raw_api)
        assert analysis.restart()
        assert analysis.tasks[0].id == 23
        assert analysis.tasks[0].status == "processing"

    request.assert_called_with(method="post", url="http://test/api-2.0/analyses/42/restart",
                               params={}, headers={})


def test_analysis_delete():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        analysis = Analysis(id=42, _raw_api=raw_api)
        assert analysis.delete()

    request.assert_called_with(method="delete", url="http://test/api-2.0/analyses/42",
                               params={}, headers={})


def test_analysis_download_archive():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        analysis = Analysis(id=42, _raw_api=raw_api)
        analysis.download_archive(output_file="test_output")

    request.assert_called_with(method="get", url="http://test/api-2.0/analyses/42/archive",
                               params={}, headers={}, output_file="test_output")


def test_analysis_download_sample():
    request = mock.Mock(return_value=None)
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        analysis = Analysis(id=42, _raw_api=raw_api)
        analysis.download_sample(output_file="test_output")

    request.assert_called_with(method="get", url="http://test/api-2.0/analyses/42/sample",
                               params={}, headers={}, output_file="test_output")


def test_analysis_cureit():
    request = mock.Mock(return_value={"status": "processing", "retries": None})
    with mock.patch("vxcube_api.raw_api.VxCubeApiRequest.request", new=request):
        raw_api = VxCubeRawApi(base_url="http://test", version=2.0)
        analysis = Analysis(id=42, _raw_api=raw_api)
        cureit = analysis.cureit()

        assert cureit.analysis_id == 42
        assert cureit.status == "processing"
        assert cureit.retries is None
        assert cureit._raw_api is raw_api

    request.assert_called_with(method="get", url="http://test/api-2.0/analyses/42/cureit",
                               params={}, headers={})


def test_analysis_update_tasks():
    values = dict(
        id=1,
        tasks=[dict(
            id=1,
            message="1"
        ), dict(
            id=2,
            message="2"
        )],
    )
    analysis = Analysis(**values)

    assert analysis.id == 1
    assert analysis.tasks[0].id == 1
    assert analysis.tasks[0].message == "1"
    assert analysis.tasks[1].id == 2
    assert analysis.tasks[1].message == "2"

    values = dict(
        id=1,
        tasks=[dict(
            id=1,
            message="111"
        ), dict(
            id=2,
            message="222"
        )],
    )
    analysis.update(**values)
    assert analysis.id == 1
    assert analysis.tasks[0].id == 1
    assert analysis.tasks[0].message == "111"
    assert analysis.tasks[1].id == 2
    assert analysis.tasks[1].message == "222"


def test_task_update():
    values = dict(
        # base
        id=1,
        status="successful",
        platform_code="winxpx86",
        start_date="2018-04-08T15:16:23.420000+00:00",
        end_date="2018-04-08T15:16:23.420000+00:00",
        suspicion=3,
    )
    task = Task(**values)

    assert task.id == 1
    assert task.status == "successful"
    assert task.message is None
    assert task.progress is None
    assert task.verdict is None
    assert task.rules is None

    values.update(dict(
        status="processing",
        message="test_message",
        progress=99,
    ))
    task.update(**values)

    assert task.message == "test_message"
    assert task.progress == 99
    assert task.verdict is None
    assert task.rules is None

    del values["message"]
    del values["progress"]
    values.update(dict(
        status="finished",
        verdict="guilty",
        rules={"neutral": ["Hugo wins the lottery"]},
    ))
    task.update(**values)

    assert task.message is None
    assert task.progress is None
    assert task.verdict == "guilty"
    assert task.rules == {"neutral": ["Hugo wins the lottery"]}


def test_subscribe_progress_for_finished():
    values = dict(
        id=1,
        tasks=[dict(
            id=1,
            status="successful"
        ), dict(
            id=2,
            status="successful"
        )],
    )
    analysis = Analysis(**values)

    with pytest.raises(VxCubeApiException):
        list(analysis.subscribe_progress())


def test_subscribe_progress():
    values = dict(
        id=1,
        _raw_api=VxCubeRawApi(base_url="http://test", version=2.0),
        tasks=[dict(
            id=1,
            status="processing"
        ), dict(
            id=2,
            status="processing"
        )],
    )
    analysis = Analysis(**values)

    ws = mock.MagicMock()
    with mock.patch("websocket.WebSocket", return_value=ws):
        with mock.patch("tortilla.Wrap.get", return_value={"id": 42}):
            list(analysis.subscribe_progress())

    assert analysis.id == 42
    ws.connect.assert_called_with("ws://test/api-2.0/ws/progress", header={"Authorization": "api-key None"})
    ws.send.assert_called_with("{\"analysis_id\": 1}")
    ws.close.assert_called_once()


def test_subscribe_progress_with_https_scheme():
    values = dict(
        id=1,
        _raw_api=VxCubeRawApi(base_url="https://test", version=2.0),
        tasks=[dict(
            id=1,
            status="processing"
        ), dict(
            id=2,
            status="processing"
        )],
    )
    analysis = Analysis(**values)
    ws = mock.MagicMock()
    ws.__iter__.return_value = iter(["{\"message\": \"test\"}"])
    with mock.patch("websocket.WebSocket", return_value=ws):
        with mock.patch("tortilla.Wrap.get", return_value={"id": 42}):
            assert list(analysis.subscribe_progress()) == [{"message": "test"}]

    assert analysis.id == 42
    ws.connect.assert_called_with("wss://test/api-2.0/ws/progress", header={"Authorization": "api-key None"})
    ws.send.assert_called_with("{\"analysis_id\": 1}")
    ws.close.assert_called_once()


def test_subscribe_progress_with_unicode_message():
    values = dict(
        id=1,
        _raw_api=VxCubeRawApi(base_url="https://test", version=2.0),
        tasks=[dict(
            id=1,
            status="processing"
        ), dict(
            id=2,
            status="processing"
        )],
    )
    analysis = Analysis(**values)
    ws = mock.MagicMock()
    ws.__iter__.return_value = iter([u"{\"message\": \"test...\"}"])
    with mock.patch("websocket.WebSocket", return_value=ws):
        with mock.patch("tortilla.Wrap.get", return_value={"id": 42}):
            assert list(analysis.subscribe_progress()) == [{"message": u"test..."}]

    assert analysis.id == 42
    ws.connect.assert_called_with("wss://test/api-2.0/ws/progress", header={"Authorization": "api-key None"})
    ws.send.assert_called_with("{\"analysis_id\": 1}")
    ws.close.assert_called_once()


def test_subscribe_progress_with_connection_close():
    values = dict(
        id=1,
        _raw_api=VxCubeRawApi(base_url="https://test", version=2.0),
        tasks=[dict(
            id=1,
            status="processing"
        )],
    )
    analysis = Analysis(**values)
    ws = mock.MagicMock()
    ws.send.side_effect = WebSocketConnectionClosedException()
    with mock.patch("websocket.WebSocket", return_value=ws), mock.patch("tortilla.Wrap.get", return_value={"id": 42}):
        list(analysis.subscribe_progress())
