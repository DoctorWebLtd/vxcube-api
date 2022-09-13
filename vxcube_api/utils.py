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
import sys
from contextlib import contextmanager

from colorlog import ColoredFormatter

from vxcube_api.errors import VxCubeApiException

UTF8_CONSOLE = hasattr(sys, "stdout") and sys.stdout and sys.stdout.encoding.lower() == "utf-8"


# py2 compatibility
try:
    str_type = basestring
except NameError:
    str_type = str


@contextmanager
def file_wrapper(file):
    if hasattr(file, "read"):
        yield file

    elif isinstance(file, str):
        with open(file, "rb") as _file:
            yield _file
    else:
        raise VxCubeApiException("FileWrapper can be used only with a path or file-like object")


def filter_data(**kwargs):
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    return kwargs


def iterator(func, count_per_request, item_key="items", **kwargs):
    offset = kwargs.pop("offset", 0)
    kwargs.pop("count", None)

    while True:
        items = func(count=count_per_request, offset=offset, **kwargs)
        offset += count_per_request
        if item_key:
            items = items[item_key]

        for item in items:
            yield item

        if len(items) == 0 or len(items) < count_per_request:
            return


def all_items(func, count_per_request, item_key="items", **kwargs):
    offset = kwargs.pop("offset", 0)
    kwargs.pop("count", None)

    _all = []
    while True:
        items = func(count=count_per_request, offset=offset, **kwargs)
        offset += count_per_request
        if item_key:
            items = items[item_key]

        if isinstance(items, list):
            _all.extend(items)
        else:
            for item in items:
                _all.append(item)

        if len(items) == 0 or len(items) < count_per_request:
            return _all


def replace_3dots(msg):
    if msg.endswith(u"\u2026"):
        return msg[:-1] + "..."
    else:
        return msg


def reencode(msg):
    return msg.encode("ascii", "replace").decode("ascii")


def message_compat(msg):
    if not UTF8_CONSOLE and isinstance(msg, str_type):
        return reencode(replace_3dots(msg))
    return msg


def root_logger_setup(level):
    colors = {
        "DEBUG": "green",
        "INFO": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }
    log_format = "%(log_color)s%(message)s"
    formatter = ColoredFormatter(log_format, log_colors=colors)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(level)
