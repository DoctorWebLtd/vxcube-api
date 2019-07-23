"""Getting a list of SHA1 of dumps from all finished analyses."""

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

from itertools import count

from vxcube_api import VxCubeApi

API_KEY = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def main():
    # Create VxCubeApi
    vxcube = VxCubeApi(api_key=API_KEY)

    number = count(start=0)
    # Get all analyses
    for analysis in vxcube.analyses_iter():
        for task in analysis.tasks:
            if task.is_success:
                for dump in task.dumps_iter():

                    # sha1 is None when dump is not available
                    if dump["sha1"] is not None:
                        print("{number}. {sha1}".format(number=next(number), sha1=dump["sha1"]))


if __name__ == "__main__":
    main()
