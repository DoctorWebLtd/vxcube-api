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

from vxcube_api.errors import VxCubeApiException
from vxcube_api.utils import all_items, file_wrapper, filter_data, iterator


def test_file_wrapper_raise():
    with pytest.raises(VxCubeApiException):
        file_wrapper({}).__enter__()


def test_file_wrapper_string():
    file = mock.mock_open(read_data=b"test_data")
    with mock.patch("vxcube_api.utils.open", file):
        with file_wrapper("test_file") as file_:
            assert file_.read() == b"test_data"

    file.assert_called_with("test_file", "rb")


def test_file_wrapper_file_like_obj():
    file = mock.Mock(**{"read.return_value": "test_data"})
    with file_wrapper(file) as file_:
        assert file_ is file


def test_filter_data():
    data = filter_data(a=[], b="", c={}, d=False, e=None)
    assert set(data.keys()) == {"a", "b", "c", "d"}


def iterable_func(total, items_key=None, type_collection=list):
    items = type_collection(range(total))

    def func(count, offset, **kwargs):
        if items_key:
            return {items_key: items[offset:offset + count]}
        return items[offset:offset + count]

    return func


def test_iterator_without_key():
    count = 0
    for i, j in enumerate(iterator(iterable_func(100), count_per_request=10, item_key=None)):
        count += 1
        assert i == j
    assert count == 100


def test_iterator_with_key():
    count = 0
    for i, j in enumerate(iterator(iterable_func(100, "i"), count_per_request=9, item_key="i")):
        count += 1
        assert i == j
    assert count == 100


def test_all_without_key():
    items = all_items(iterable_func(100), count_per_request=10, item_key=None)
    assert len(items) == 100


def test_all_with_key():
    items = all_items(iterable_func(100, "i"), count_per_request=9, item_key="i")
    assert len(items) == 100


def test_all_with_key_and_tuple():
    items = all_items(iterable_func(100, "i", tuple), count_per_request=9, item_key="i")
    assert len(items) == 100
