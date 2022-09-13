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
from functools import wraps

from requests_toolbelt.multipart.encoder import MultipartEncoder

from vxcube_api.errors import VxCubeApiException
from vxcube_api.objects import (Analysis, Format, License, Platform, Sample,
                                Session, Task)
from vxcube_api.raw_api import VxCubeRawApi
from vxcube_api.utils import file_wrapper, filter_data, iterator

logger = logging.getLogger(__name__)


def return_objects(obj, add_raw_api=False):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            data = func(self, *args, **kwargs)

            def create_obj(kw):
                if add_raw_api:
                    kw["_raw_api"] = self._raw_api
                return obj(**kw)

            if isinstance(data, dict):
                logger.debug("Create %s object", type(obj).__name__)
                return create_obj(data)
            elif isinstance(data, (list, tuple, set)):
                logger.debug("Create %d %s objects", len(data), type(obj).__name__)
                results = []
                for item in data:
                    results.append(create_obj(item))
                return results
            else:
                return None

        return wrapper

    return decorator


class VxCubeApi(object):

    def __init__(self, api_key=None, base_url="https://vxcube.drweb.com/", version=2.0):
        self._raw_api = VxCubeRawApi(api_key, base_url, version)

    def login(self, login, password, new_key=False):
        """
        Get API key using login and password.

        :param str login:
        :param str password:
        :return None:
        :raises VxCubeApiException, VxCubeApiHttpException
        """
        logger.debug("Login with %s", login)
        if self._raw_api.api_key:
            logger.info("Use login with existing API key")

        data = filter_data(
            login=login,
            password=password,
            new_key=new_key
        )
        response = self._raw_api.login.post(json=data)

        if not isinstance(response, dict) or "api_key" not in response:
            logger.error("Unknown server response")
            raise VxCubeApiException("Incorrect server response")

        self._raw_api.api_key = response["api_key"]

    @return_objects(Session, add_raw_api=True)
    def sessions(self):
        """
        Get a list of open sessions.

        :return list[Session]: sessions
        :raises VxCubeApiHttpException
        """
        logger.debug("Get sessions")
        return self._raw_api.sessions.get()

    @return_objects(Format)
    def formats(self):
        """
        Get a list of supported formats.

        :return list[Format]: formats
        :raises VxCubeApiHttpException
        """
        logger.debug("Get formats")
        return self._raw_api.formats.get()

    @return_objects(Platform)
    def platforms(self):
        """
        Get a list of supported platforms.

        :return list[Platform]: platforms
        :raises VxCubeApiHttpException
        """
        logger.debug("Get platforms")
        return self._raw_api.platforms.get()

    @return_objects(License)  # noqa: A003
    def license(self):  # noqa: A003
        """
        Get information about current license.

        :return License: license
        :raises VxCubeApiHttpException
        """
        logger.debug("Get license")
        return self._raw_api.license.get()

    @return_objects(Sample, add_raw_api=True)
    def samples(self, sample_id=None, count=None, offset=None, md5=None, sha1=None, sha256=None,
                format_name=None, format_group_name=None):
        """
        Get sample by ID or get a filtered list of samples.

        :param int sample_id:
        :param int count:
        :param int offset:
        :param str md5:
        :param str sha1:
        :param str sha256:
        :param str format_name:
        :param str format_group_name:
        :return List[Sample] or Sample:
        :raises VxCubeApiHttpException
        """
        if sample_id:
            logger.debug("Get sample")
            return self._raw_api.samples.get(sample_id)

        logger.debug("Get list of samples")
        data = filter_data(
            count=count,
            offset=offset,
            md5=md5,
            sha1=sha1,
            sha256=sha256,
            format_name=format_name,
            format_group_name=format_group_name
        )
        return self._raw_api.samples.get(json=data)

    def samples_iter(self, count_per_request=100, **kwargs):
        """
        Iterate over self.samples.

        :param count_per_request:
        :param kwargs:
        :return:
        """
        logger.debug("Use sample iterator")
        kwargs.pop("sample_id", None)
        return iterator(func=self.samples, count_per_request=count_per_request, item_key=None, **kwargs)

    def _upload_sample(self, file):
        logger.debug("Upload sample to server")
        with file_wrapper(file) as file:
            fields = {"file": (file.name, file, "application/octet-stream")}
            enc = MultipartEncoder(fields=fields)
            headers = {"Content-Type": enc.content_type}
            return self._raw_api.samples.post(data=enc, headers=headers)

    @return_objects(Sample, add_raw_api=True)
    def upload_sample(self, file):
        """
        Upload sample to Dr.Web vxCube server.

        :param str or file-like object file: path or file-like object
        :return Sample:
        :raises VxCubeApiHttpException
        """
        return self._upload_sample(file)

    @return_objects(Sample, add_raw_api=True)
    def upload_samples(self, file):
        """
        Upload samples to Dr.Web vxCube server.

        :param str or file-like object file: path or file-like object
        :return list[Sample]:
        :raises VxCubeApiHttpException
        """
        result = self._upload_sample(file)
        if "samples" in result:
            return result["samples"]
        else:
            return [result]

    @return_objects(Analysis, add_raw_api=True)
    def analyses(self, analysis_id=None, count=None, offset=None, format_group_name=None):
        """
        Get analysis by ID or get a filtered list of analyses.

        :param int analysis_id:
        :param int count:
        :param int offset:
        :param str format_group_name:
        :return Analysis or list[Analysis]:
        :raises VxCubeApiHttpException
        """
        if analysis_id:
            logger.debug("Get analysis")
            return self._raw_api.analyses.get(analysis_id)

        logger.debug("Get analysis list")
        data = filter_data(
            count=count,
            offset=offset,
            format_group_name=format_group_name
        )
        return self._raw_api.analyses.get(json=data)

    def analyses_iter(self, count_per_request=100, **kwargs):
        """
        Iterate over self.analyses.

        :param count_per_request:
        :param kwargs:
        :return:
        """
        logger.debug("Use analysis iterator")
        kwargs.pop("analysis_id", None)
        return iterator(func=self.analyses, count_per_request=count_per_request, item_key=None, **kwargs)

    @return_objects(Analysis, add_raw_api=True)
    def start_analysis(self, sample_id, platforms, analysis_time=None, format_name=None,
                       custom_cmd=None, generate_cureit=None, drop_size_limit=None, net=None, copylog=False,
                       crypto_api_limit=64, dump_size_limit=64, flex_time=False, forwards=None, get_lib=False,
                       injects_limit=100, monkey_clicker=None, dump_browsers=True, dump_mapped=True,
                       dump_ssdt=True, no_clean=False, optional_count=None, proc_lifetime=None, set_date=None,
                       userbatch=None, dump_processes=True, write_file_limit=512):
        """
        Start sample analysis.

        :param int sample_id:
        :param list platforms:
        :param int analysis_time:
        :param str format_name:
        :param str custom_cmd:
        :param bool generate_cureit:
        :param int drop_size_limit:
        :param str net:
        :param bool copylog:
        :param int crypto_api_limit:
        :param int dump_size_limit:
        :param bool flex_time:
        :param list forwards:
        :param bool get_lib:
        :param int injects_limit:
        :param bool monkey_clicker:
        :param bool dump_browsers:
        :param bool dump_mapped:
        :param bool dump_ssdt:
        :param bool no_clean:
        :param int optional_count:
        :param int proc_lifetime:
        :param str set_date:
        :param str userbatch:
        :param bool dump_processes:
        :param int write_file_limit:
        :return Analyse:
        :raises VxCubeApiHttpException
        """
        logger.debug("Start analysis")
        data = filter_data(
            sample_id=sample_id,
            platforms=platforms,
            analysis_time=analysis_time,
            format_name=format_name,
            custom_cmd=custom_cmd,
            generate_cureit=generate_cureit,
            drop_size_limit=drop_size_limit,
            net=net,
            copylog=copylog,
            crypto_api_limit=crypto_api_limit,
            dump_size_limit=dump_size_limit,
            flex_time=flex_time,
            forwards=forwards,
            get_lib=get_lib,
            injects_limit=injects_limit,
            monkey_clicker=monkey_clicker,
            dump_browsers=dump_browsers,
            dump_mapped=dump_mapped,
            dump_ssdt=dump_ssdt,
            dump_processes=dump_processes,
            no_clean=no_clean,
            optional_count=optional_count,
            proc_lifetime=proc_lifetime,
            set_date=set_date,
            write_file_limit=write_file_limit
        )
        if userbatch:
            with file_wrapper(userbatch) as file:
                return self._raw_api.analyses.post(files={"userbatch": (file.name, file, "application/octet-stream")},
                                                   data=data)
        return self._raw_api.analyses.post(json=data)

    @return_objects(Task, add_raw_api=True)
    def task(self, task_id):
        """
        Get task data.

        :param int task_id:
        :return Task:
        """
        logger.debug("Get task")
        return self._raw_api.tasks(task_id).get()
