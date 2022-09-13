"""Checks there is no such file uploaded already and analise it."""

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

import hashlib
import sys
import time

from vxcube_api import VxCubeApi
from vxcube_api.errors import VxCubeApiHttpException

API_KEY = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

# Create VxCubeApi
vxcube = VxCubeApi(api_key=API_KEY)


def sha256sum(filepath):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filepath, "rb", buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


def start_analysis(sample, poll_progress=True):
    if not sample.format_name or not sample.platforms:
        print("Unknown file type or platforms list")
        return

    # Analise only on first two platforms
    platforms = sample.platforms[:2]
    print("Starting analysis for {sample.id} on {platforms}:".format(sample=sample, platforms=platforms))
    analysis = vxcube.start_analysis(sample_id=sample.id, platforms=platforms)

    if poll_progress:
        tasks_format = {}
        for task in analysis.tasks:
            tasks_format[task.id] = "[{task.platform_code:<13}] [{{progress}}%] {{message}}".format(task=task)

        # Monitoring analysis progress with WebSocket polling mechanism
        for progress in analysis.subscribe_progress():
            print(tasks_format[progress["task_id"]].format(**progress))
    else:
        # Or just check 'is_finished' status
        while not analysis.is_finished:
            print("  Current progress: {}%".format(int(analysis.total_progress)))
            time.sleep(20)
            # WARN: It's make HTTP GET request each time to check is it finished
            analysis.refresh()

    # Print results
    print("Analysis finished:")
    for task in analysis.tasks:
        print("  Task[{task.id}] finished '{task.status}'. Maliciousness: {task.maliciousness}".format(task=task))


def submit(filepath, sha256=None):
    # Calculate SHA256 of file
    sha256 = sha256 or sha256sum(filepath)

    # Search for samples
    samples = vxcube.samples(sha256=sha256, count=10)
    if samples:
        print("Sample {sample.sha256} (format: '{sample.format_name}') "
              "has been submitted already: ".format(sample=samples[0]))
        for sample in samples:
            print("  [{sample.id}] Uploaded at {sample.upload_date}".format(sample=sample))
        return

    # Upload file
    try:
        # WARN: For EML/ZIP/etc we can get several samples uploaded
        samples = vxcube.upload_samples(filepath)
        print("Sample has been uploaded successfully:")
        for sample in samples:
            print("  [{sample.id}] {sample.sha256} "
                  "(format: '{sample.format_name}', platforms: {sample.platforms})".format(sample=sample))
        print()
    except VxCubeApiHttpException as e:
        if e.code == 400:
            print(e)
        return

    # Start analysis
    for sample in samples:
        start_analysis(sample)


def main():
    submit(sys.argv[1])


if __name__ == "__main__":
    main()
