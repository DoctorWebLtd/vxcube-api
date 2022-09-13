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

import json
import logging
from collections import namedtuple

import dateutil.parser
import websocket
from requests.compat import urlparse

from vxcube_api.errors import VxCubeApiException
from vxcube_api.utils import filter_data, iterator

logger = logging.getLogger(__name__)

Format = namedtuple("Format", ("name", "group_name", "platforms"))
Platform = namedtuple("Platform", ("code", "name", "os_code"))
BaseLicense = namedtuple("License", ("start_date", "end_date", "uploads_spent", "uploads_total",
                                     "vnc_allowed", "cureit_allowed", "upload_max_size", "max_run_time"))


def _convert_time(strtime):
    if not strtime:
        return None
    return dateutil.parser.parse(strtime)


class License(BaseLicense):
    _time_fields = ("start_date", "end_date")

    def __new__(cls, **kwargs):
        for key in kwargs:
            if key in cls._time_fields:
                kwargs[key] = _convert_time(kwargs[key])
        return super(License, cls).__new__(cls, **kwargs)


class ApiObject(object):
    __slots__ = ("_raw_api",)
    _time_fields = ()

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def update(self, **kwargs):
        all_slots = {item
                     for slots in (getattr(cls, "__slots__", []) for cls in type(self).__mro__)
                     for item in slots}

        for key in kwargs:
            if key in all_slots:
                if key in self._time_fields:
                    setattr(self, key, _convert_time(kwargs[key]))
                else:
                    setattr(self, key, kwargs[key])


class Session(ApiObject):
    __slots__ = ("api_key", "start_date")
    _time_fields = ("start_date",)

    def delete(self):
        logger.debug("Delete session")
        self._raw_api.sessions.delete(self.api_key)
        return True


class Sample(ApiObject):
    __slots__ = ("id", "name", "size", "format_name", "upload_date",
                 "md5", "sha1", "sha256", "is_x64", "platforms")
    _time_fields = ("upload_date",)

    @property
    def _api(self):
        if getattr(self, "_raw_api", None) is None:
            raise VxCubeApiException("Sample is not bound to API")
        return self._raw_api.samples(self.id)

    def download(self, output_file):
        logger.debug("Download sample")
        return self._api.download.get(output_file=output_file)


class CureIt(ApiObject):
    __slots__ = ("status", "retries", "analysis_id", "task_id")

    def __init__(self, **kwargs):
        kwargs.setdefault("analysis_id", None)
        kwargs.setdefault("task_id", None)
        super(CureIt, self).__init__(**kwargs)

        if not self.analysis_id and not self.task_id:
            raise VxCubeApiException("CureIt is not bound to Analysis or Task")

    def __repr__(self):
        """Format repr depending on input data."""
        if self.analysis_id:
            _type = "Analysis"
            _id = self.analysis_id
        else:
            _type = "Task"
            _id = self.task_id

        return "CureIt ({type}[{id}]) status: {status}".format(type=_type, id=_id, status=self.status)

    @property
    def _api(self):
        if self.analysis_id:
            return self._raw_api.analyses(self.analysis_id)
        return self._raw_api.tasks(self.task_id)

    @property
    def is_success(self):
        if self.status == "successful":
            return True
        return False

    @property
    def is_failed(self):
        if self.status == "failed":
            return True
        return False

    @property
    def is_deleted(self):
        if self.status == "deleted":
            return True
        return False

    @property
    def is_finished(self):
        if self.status == "processing":
            return False
        return True

    @property
    def is_processing(self):
        return not self.is_finished

    @property
    def is_small_file(self):
        if self.status == "small_file":
            return True
        return False

    @property
    def can_retrying(self):
        if self.is_deleted or (self.is_failed and (not self.retries or "after" not in self.retries)):
            return True
        return False

    def download(self, output_file):
        logger.debug("Download CureIt!", self.task_id)
        return self._api.get("cureit.exe", output_file=output_file)

    def retry(self):
        logger.debug("Retry to create CureIt!")
        data = self._api.cureit.put()
        if not isinstance(data, dict):
            logger.info("Unknown response")
            return False
        self.update(**data)
        return True


class Task(ApiObject):
    _variable_slots = (
        "message", "progress",  # processing task
        "verdict", "rules"  # successful task
    )

    __slots__ = _variable_slots + (
        "id", "status", "platform_code", "start_date", "end_date", "maliciousness",  # basic task
    )

    _time_fields = ("start_date", "end_date")

    def update(self, **kwargs):
        if "status" in kwargs and kwargs["status"] != getattr(self, "status", None):
            for sl in self._variable_slots:
                kwargs.setdefault(sl, None)
        super(Task, self).update(**kwargs)

    @property
    def _api(self):
        return self._raw_api.tasks(self.id)

    @property
    def is_success(self):
        if self.status == "successful":
            return True
        return False

    @property
    def is_failed(self):
        if self.status == "failed":
            return True
        return False

    @property
    def is_deleted(self):
        if self.status == "deleted":
            return True
        return False

    @property
    def is_finished(self):
        if self.status == "in queue" or self.status == "processing":
            return False
        return True

    @property
    def is_processing(self):
        return not self.is_finished

    @property
    def is_android(self):
        return self.platform_code.startswith("android")

    def cureit(self):
        if self.is_android:
            return None

        logger.debug("Get CureIt! of task %d", self.id)
        data = self._api.cureit.get()
        if not isinstance(data, dict):
            logger.info("Unknown response")
            return None

        return CureIt(task_id=self.id, _raw_api=self._raw_api, **data)

    def dumps(self, count=None, offset=None, search=None):
        logger.debug("Get dumps of task %d", self.id)
        data = filter_data(
            count=count,
            offset=offset,
            search=search
        )
        return self._api.dumps.get(json=data)

    def dumps_iter(self, count_per_request=100, search=None):
        logger.debug("Use dump iterator")
        return iterator(func=self.dumps, count_per_request=count_per_request, search=search)

    def drops(self, count=None, offset=None, search=None):
        logger.debug("Get drops of task %d", self.id)
        data = filter_data(
            count=count,
            offset=offset,
            search=search
        )
        return self._api.drops.get(json=data)

    def drops_iter(self, count_per_request=100, search=None):
        logger.debug("Use drop iterator")
        return iterator(func=self.drops, count_per_request=count_per_request, search=search)

    def networks(self, count=None, offset=None, search=None):
        logger.debug("Get networks of task %d", self.id)
        data = filter_data(
            count=count,
            offset=offset,
            search=search
        )
        return self._api.networks.get(json=data)

    def networks_iter(self, count_per_request=100, search=None):
        logger.debug("Use network iterator")
        return iterator(func=self.networks, count_per_request=count_per_request, search=search)

    def apilog(self, count=None, offset=None, search=None):
        logger.debug("Get API log of task %d", self.id)
        data = filter_data(
            count=count,
            offset=offset,
            search=search
        )
        return self._api.api_log.get(json=data)

    def apilog_iter(self, count_per_request=100, search=None):
        logger.debug("Use API-log iterator")
        return iterator(func=self.apilog, count_per_request=count_per_request, search=search)

    def intents(self, count=None, offset=None, search=None):
        logger.debug("Get intents of task %d", self.id)
        data = filter_data(
            count=count,
            offset=offset,
            search=search
        )
        return self._api.intents.get(json=data)

    def intents_iter(self, count_per_request=100, search=None):
        logger.debug("Use intent iterator")
        return iterator(func=self.intents, count_per_request=count_per_request, search=search)

    def phone_actions(self, count=None, offset=None, search=None):
        logger.debug("Get phone actions of task %d", self.id)
        data = filter_data(
            count=count,
            offset=offset,
            search=search
        )
        return self._api.phone_actions.get(json=data)

    def phone_actions_iter(self, count_per_request=100, search=None):
        logger.debug("Use phone-action iterator")
        return iterator(func=self.phone_actions, count_per_request=count_per_request, search=search)

    def storage_lists(self):
        logger.debug("Get a list of files and directories in archive")
        return self._api.archive_storage.get()

    def download_storage_file(self, path, output_file):
        logger.debug("Download file %s from archive", path)
        data = {"path": path}
        return self._api.archive_storage.get(json=data, output_file=output_file)

    def restart(self):
        if not self.is_failed and not self.is_deleted:
            logger.info("Task cannot be restarted")
            return False

        logger.debug("Restart task %d", self.id)
        data = self._api.restart.post()
        self.update(**data)
        return True

    def download_archive(self, output_file):
        logger.debug("Download archive of task %d", self.id)
        return self._api.archive.get(output_file=output_file)

    def download_report(self, output_file):
        logger.debug("Download report of task %d", self.id)
        return self._api.report.get(output_file=output_file)

    def download_sample(self, output_file):
        logger.debug("Download sample of task %d", self.id)
        return self._api.sample.get(output_file=output_file)


class Analysis(ApiObject):
    __slots__ = ("id", "sha1", "sample_id", "size", "format_name", "start_date", "user_name", "tasks")
    _time_fields = ("start_date",)

    def update(self, **kwargs):
        tasks = kwargs.pop("tasks", [])

        if hasattr(self, "tasks"):
            for task in tasks:
                self._update_task_by_id(task.get("id"), task)
        else:
            _raw_api = kwargs.get("_raw_api")
            kwargs["tasks"] = []
            for task in tasks:
                kwargs["tasks"].append(Task(_raw_api=_raw_api, **task))
        super(Analysis, self).update(**kwargs)

    @property
    def _api(self):
        return self._raw_api.analyses(self.id)

    def _update_task_by_id(self, task_id, data):
        for task_obj in self.tasks:
            if task_obj.id == task_id:
                logger.debug("Update task %d from analysis %d", task_id, self.id)
                task_obj.update(**data)
                return task_obj

    @property
    def is_finished(self):
        return all(task.is_finished for task in self.tasks)

    @property
    def is_processing(self):
        return not self.is_finished

    @property
    def total_progress(self):
        total = 0
        for task in self.tasks:
            if task.is_processing:
                total += task.progress
            else:
                total += 100
        return total / len(self.tasks)

    def restart(self):
        logger.debug("Restart analysis %d", self.id)
        data = self._api.restart.post()

        tasks = data.pop("tasks", [])
        for task in tasks:
            self._update_task_by_id(task["id"], task)

        self.update(**data)
        return True

    def delete(self):
        logger.debug("Delete analysis %d", self.id)
        self._api.delete()
        return True

    def download_archive(self, output_file):
        logger.debug("Download archive of analysis %d", self.id)
        return self._api.archive.get(output_file=output_file)

    def download_sample(self, output_file):
        logger.debug("Download sample of analysis %d", self.id)
        return self._api.sample.get(output_file=output_file)

    def cureit(self):
        logger.debug("Get CureIt! of analysis %d", self.id)
        data = self._api.cureit.get()
        if not isinstance(data, dict):
            logger.info("Unknown response")
            return None

        return CureIt(analysis_id=self.id, _raw_api=self._raw_api, **data)

    def refresh(self):
        self.update(**self._api().get())

    def subscribe_progress(self):
        if self.is_finished:
            logger.debug("Cannot subscribe to analysis %d because it is finished", self.id)
            raise VxCubeApiException("All tasks finished")

        ws = websocket.WebSocket()
        url_parts = urlparse(self._raw_api.ws.progress.url())
        if url_parts.scheme == "https":
            url_parts = url_parts._replace(scheme="wss")
        else:
            url_parts = url_parts._replace(scheme="ws")

        try:
            logger.debug("Try to connect to analysis %d", self.id)
            ws.connect(url_parts.geturl(), header=self._raw_api._api_request.headers)
            logger.debug("Send analysis_id=%d", self.id)
            ws.send(json.dumps({"analysis_id": self.id}))

            for msg in ws:
                # Signal: ws is closed
                if not msg:
                    break

                yield json.loads(msg)

        except websocket.WebSocketConnectionClosedException:
            # ws is closed, return from function
            logger.debug("WebSocket closed")

        finally:
            ws.close()
            # Just final results update
            self.refresh()
