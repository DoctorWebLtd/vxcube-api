"""Using raw API to interact with API 1.0."""

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

from vxcube_api.raw_api import VxCubeRawApi
from vxcube_api.utils import file_wrapper

FILE_PATH = "/path/to/sample"
API_KEY = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def main():
    # Create raw API
    api = VxCubeRawApi(api_key=API_KEY, version=1.0)

    # Upload sample
    with file_wrapper(FILE_PATH) as file:
        rs = api.create.post(files=file, data={"analyse_time": 5.0, "winxpx86": True})

    # Get analysis data
    analysis_id = rs["url"].split("/")[-1]
    rs = api.report.get(analysis_id)
    print(rs)
    if all(task["status"] != "processing" for task in rs["tasks"]):
        print("All tasks finished")


if __name__ == "__main__":
    main()
