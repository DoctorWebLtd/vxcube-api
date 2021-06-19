[![Build Status](https://travis-ci.org/DoctorWebLtd/vxcube-api.svg?branch=master)](https://travis-ci.org/DoctorWebLtd/vxcube-api/)
[![Coverage Status](https://coveralls.io/repos/github/DoctorWebLtd/vxcube-api/badge.svg?branch=master)](https://coveralls.io/github/DoctorWebLtd/vxcube-api?branch=master)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/vxcube-api.svg)](https://pypi.org/project/vxcube-api/)

# vxcube-api package
vxcube-api is an API client for interacting with Dr.Web vxCube.

## Installation
Python 2.7 or later is required to be installed in advance.
Install vxcube-api either from the Python Package Index (PyPI):
```bash
$ pip install -U vxcube-api
```
or from source:
```bash
$ python setup.py install
```

## Using command line
Dr.Web vxCube API Client supports command line. To get information about available commands, use `--help`:
```bash
$ vxcube_client --help
```

Command list:

| Command            | Description                                                             |
| ------------------ | ----------------------------------------------------------------------- |
| login              | Get an API key which must be specified in all other commands            |
| config             | Save or delete `base-url`, `version`, or `api-key` parameter values     |
| upload             | Upload sample to Dr.Web vxCube server                                   |
| analyse            | Analyse uploaded file                                                   |
| delete             | Delete analysis results                                                 |
| download sample    | Download sample                                                         |
| download archive   | Download archive with analysis results                                  |
| subscribe-analysis | Get real-time data about analysis progress                              |
 
Example:
```bash
$ vxcube_client config  --api-key aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
$ vxcube_client upload /path/to/sample
Sample uploaded successful:
    sample_path [id: 2342]
        - format: exe
        - platforms: ['winxpx86', 'win7x86', 'win7x64', 'win10x64']
$ vxcube_client analyse 2342 -p win7x86 -p win10x64 --time 30
$ vxcube_client subscribe-analysis d4e22a38-6bdc-4902-881d-897687023c30
... 
[win7x86 ] [50%] Waiting for the 3580 (0xdfc) process to be dumped...
[win10x64] [20%] File is running (19 of 30 sec remaining)...
...
All tasks finished:
Task[48151]-win7x86 [successful] maliciousness: 0
Task[62342]-win10x64 [successful] maliciousness: 25
```

## VxCubeApi class
You can write your own script for processing files with VxCubeApi class.

```python
from vxcube_api import VxCubeApi

API_KEY = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def main():
    # Create VxCubeApi
    vxcube = VxCubeApi(api_key=API_KEY)

    # Upload sample
    sample = vxcube.upload_sample("sample_path")
    msg = "Sample uploaded successfully: {sample.id}, {sample.format_name}, {sample.platforms}"
    print(msg.format(sample=sample))

    # Start analysis
    analysis = vxcube.start_analysis(
        sample_id=sample.id,
        platforms=sample.platforms[0:2],
        analysis_time=30
    )
    for msg_obj in analysis.subscribe_progress():
        print(msg_obj)

    # Print results
    print("Analysis finished")
    msg = "Task[{task.id}] is {task.status}. Maliciousness: {task.maliciousness}"
    for task in analysis.tasks:
        print(msg.format(task=task))


if __name__ == '__main__':
    main()

```

## More examples
More usage examples are available [here](https://github.com/DoctorWebLtd/vxcube-api/tree/master/examples).