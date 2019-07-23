## Using command line

Get `api-key`
```bash
$ vxcube_client login --login "example@drweb.com"
Password: <password>
Session started with API key aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
```

Save `api-key` so you don't have to specify it in each request
```bash
$ vxcube_client config  --api-key aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
```

Upload sample to Dr.Web vxCube server 
```bash
$ vxcube_client upload /path/to/sample
Sample uploaded successful:
    sample_path [id: 2342]
        - format: exe
        - platforms: ['winxpx86', 'win7x86', 'win7x64', 'win10x64']
```
 
Start sample analysis
```bash
$ vxcube_client analyse 2342 -p win7x86 -p win10x64 --time 30 
Analysis 1516 started
```

Get real-time data about analysis progress
```bash
$ vxcube_client subscribe_analysis 1516
... 
[win7x86 ] [50%] Waiting for the 3580 (0xdfc) process to be dumped...
[win10x64] [20%] File is running (19 of 30 sec remaining)...
...
All tasks finished:
Task[48151]-win7x86 [successful] maliciousness: 0
Task[62342]-win10x64 [successful] maliciousness: 25
```

Download archive with analysis results
```bash
$ vxcube_client download archive --task-id 62342
Archive downloaded to <current_dir>/win10x64_archive.zip.
```
