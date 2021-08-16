import json
import os

import boto3
from botocore.exceptions import ClientError

INPUT_BUCKET = os.getenv('IN_BUCKET')
OUT_BUCKET = os.getenv('OUT_BUCKET')
QUEUE_ARN = os.getenv('QUEUE_ARN')
QUEUE_ROLE = os.getenv('QUEUE_ROLE')


def make_input(name):
    filename = f's3://{INPUT_BUCKET}/{name}'
    return {
        "AudioSelectors": {
            "Audio Selector 1": {
                "Offset": 0,
                "DefaultSelection": "DEFAULT",
                "ProgramSelection": 1
            }
        },
        "VideoSelector": {
            "ColorSpace": "FOLLOW",
            "Rotate": "DEGREE_0",
            "AlphaBehavior": "DISCARD"
        },
        "FilterEnable": "AUTO",
        "PsiControl": "USE_PSI",
        "FilterStrength": 0,
        "DeblockFilter": "DISABLED",
        "DenoiseFilter": "DISABLED",
        "InputScanType": "AUTO",
        "TimecodeSource": "ZEROBASED",
        "FileInput": filename
    }


def make_job(inputs, name_modifier, task_token):
    task_token1 = task_token[0:256]
    task_token2 = task_token[256:512]
    task_token3 = task_token[512:768]

    with open('job.json') as f:
        job_str = f.read()

    job_str = job_str.replace('**name_modifier**', name_modifier)
    job_str = job_str.replace('**bucketname**', OUT_BUCKET)
    job_str = job_str.replace('**task_token1**', task_token1)
    job_str = job_str.replace('**task_token2**', task_token2)
    job_str = job_str.replace('**task_token3**', task_token3)


    job = json.loads(job_str)
    job["Settings"]["Inputs"] = inputs
    job["Queue"] = QUEUE_ARN
    job["Role"] = QUEUE_ROLE

    return job


def handler(event, context):
    '''
    Here is an example of what the event list will look like.
    ```
    {'Input': [{'ExecutedVersion': '$LATEST', 'Payload': {'position': 1, 'name': '964746682/60-95.mkv', 'render': True}, 'SdkHttpMetadata': {'AllHttpHeaders': {'X-Amz-Executed-Version': ['$LATEST'], 'x-amzn-Remapped-Content-Length': ['0'], 'Connection': ['keep-alive'], 'x-amzn-RequestId': ['af226660-42dd-4d2c-8b3e-d59c28a0a2f5'], 'Content-Length': ['62'], 'Date': ['Mon, 16 Aug 2021 00:22:16 GMT'], 'X-Amzn-Trace-Id': ['root=1-6119afb3-13965a7e51e7742f48d81bdf;parent=6c765cbde11a8bba;sampled=1'], 'Content-Type': ['application/json']}, 'HttpHeaders': {'Connection': 'keep-alive', 'Content-Length': '62', 'Content-Type': 'application/json', 'Date': 'Mon, 16 Aug 2021 00:22:16 GMT', 'X-Amz-Executed-Version': '$LATEST', 'x-amzn-Remapped-Content-Length': '0', 'x-amzn-RequestId': 'af226660-42dd-4d2c-8b3e-d59c28a0a2f5', 'X-Amzn-Trace-Id': 'root=1-6119afb3-13965a7e51e7742f48d81bdf;parent=6c765cbde11a8bba;sampled=1'}, 'HttpStatusCode': 200}, 'SdkResponseMetadata': {'RequestId': 'af226660-42dd-4d2c-8b3e-d59c28a0a2f5'}, 'StatusCode': 200}, {'ExecutedVersion': '$LATEST', 'Payload': {'position': 2, 'name': '964746682/100-110.mkv', 'render': True}, 'SdkHttpMetadata': {'AllHttpHeaders': {'X-Amz-Executed-Version': ['$LATEST'], 'x-amzn-Remapped-Content-Length': ['0'], 'Connection': ['keep-alive'], 'x-amzn-RequestId': ['c322707e-c65e-46f9-b1d3-e57795873842'], 'Content-Length': ['64'], 'Date': ['Mon, 16 Aug 2021 00:22:15 GMT'], 'X-Amzn-Trace-Id': ['root=1-6119afb3-13965a7e51e7742f48d81bdf;parent=3744adb25e323391;sampled=1'], 'Content-Type': ['application/json']}, 'HttpHeaders': {'Connection': 'keep-alive', 'Content-Length': '64', 'Content-Type': 'application/json', 'Date': 'Mon, 16 Aug 2021 00:22:15 GMT', 'X-Amz-Executed-Version': '$LATEST', 'x-amzn-Remapped-Content-Length': '0', 'x-amzn-RequestId': 'c322707e-c65e-46f9-b1d3-e57795873842', 'X-Amzn-Trace-Id': 'root=1-6119afb3-13965a7e51e7742f48d81bdf;parent=3744adb25e323391;sampled=1'}, 'HttpStatusCode': 200}, 'SdkResponseMetadata': {'RequestId': 'c322707e-c65e-46f9-b1d3-e57795873842'}, 'StatusCode': 200}], 'TaskToken': 'AAAAKgAAAAIAAAAAAAAAAYGlS7L8DvCUCZJHQwSAd0N6rCIFCQHNQTzyuujBqoxEWAEGin6LeZEoiDH0NFJVfoy1pMNXkAikZTonLyQCFiff8vLh91hATjQlWd+yAu1jedliZMakwZsLus7X+qMmf2F58E86p9IZU0EVEaiFR7y7bXjylqQC0c4o9EXcrEZddN7jEnP0rtXMjsBXrnPOGLPNqX6b+oEJMgZQKXQ9gQjebOOa0vlrpg1JP4rCyt3nBbMRhhe3jTKNEAwdQRV4d5z8W3RnhI/1fDyZUw9gv/Rz2ySB5zL3/BwHVWgEouQxJlzW1iDQCRXQobYawrCDbV+DRYmPGZSTNAQ197dqDn2J5naPy73VeNJcn5HXj8SQQLADET+7jiT+2BHfoAgWQ9X7F6gn7QZu9jJcdBYjeip8WZyAvVajmUL9KHOPoHa/lij+CQMjbNXV7iT5P3Y/fNL4pP6pQAc/2VzpyOkz5bx7jLEnvvs8B8L8wjtwkJ/0n0lw0ikHkpvdignTvQTo4hw/GnECWb2QdSHlI15fdCW2OSVMRlFtFvqwyEJz7kMhi7zWOuRKJw2y+IQS8DC3/QoEjXebmHjzgeiQyONQxB19nfKRbVnnZeNARqTQhnl1tTGkcrw7XdqgGFVS65vcJA=='}
    ```

    The "Payload" attribute contains the data we need to contatenate the clips together.
    All of that data will be concatenated into the `clips` variable that will be used to construct the
    MediaConvert Object.
    '''
    print(event)
    clips = []
    task_token = event['TaskToken']

    for item in event['Input']:
        payload = item.get('Payload')
        if not payload is None:
            clips.append(payload)

    clip = clips[0]
    twitch_video_id = clip['name'].split('/')[0]

    sorted(clips, key=lambda clip: clip['position'])

    inputs = []
    for clip in clips:
        inputs.append(make_input(clip['name']))

    job_object = make_job(inputs, twitch_video_id, task_token)

    mediaconvert_client = boto3.client(  # need endpoint url to start mediaconvert
        'mediaconvert', endpoint_url='https://lxlxpswfb.mediaconvert.us-east-1.amazonaws.com')
    mediaconvert_client.create_job(**job_object)

    return {}
