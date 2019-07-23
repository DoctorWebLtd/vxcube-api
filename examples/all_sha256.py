"""3 different ways of getting SHA256 of all samples."""

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

from vxcube_api import VxCubeApi
from vxcube_api.utils import all_items, iterator

API_KEY = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def main():
    # Create VxCubeApi
    api = VxCubeApi(api_key=API_KEY, version=2.0)

    sha256 = set()
    # Use samples_iter of VxCubeApi
    for sample in api.samples_iter():
        sha256.add(sample.sha256)

    # Use iterator
    for sample in iterator(api.samples, count_per_request=100, item_key=None):
        assert sample.sha256 in sha256

    # Use all_items
    all_sha256 = {s.sha256 for s in all_items(api.samples, count_per_request=100, item_key=None)}
    assert sha256 == all_sha256
    print(sha256)


if __name__ == "__main__":
    main()
