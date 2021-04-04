import json
import os

import boto3
from botocore.exceptions import ClientError


def make_input(name):
    input_bucket = os.getenv('IN_BUCKET')
    filename = f's3://{input_bucket}/{name}'
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

def make_job(inputs):

    output_bucket = os.getenv('OUT_BUCKET')
    job_str = ''
    with open('job.json') as f:
        job_str = f.read()

    job_str = job_str.replace('**name_modifier**', output_bucket)
    job = json.loads(job_str)
    job["Settings"]["Inputs"] = inputs
    job["Queue"] = os.getenv('QUEUE_ARN')

    return job
    

def handler(event, context):
    '''
    Here is an example of what the event list will look like.
    ```
    [{'ExecutedVersion': '$LATEST', 'Payload': {'position': 12, 'name': 'a91a0ee5-c7e8-4ba1-b91b-ccdcb593e623-clip12.mkv'},
    'SdkHttpMetadata': {'AllHttpHeaders': {'X-Amz-Executed-Version': ['$LATEST'], 'x-amzn-Remapped-Content-Length': ['0'], 
    'Connection': ['keep-alive'], 'x-amzn-RequestId': ['c59e6cdb-f51c-4897-b1d3-04cbead3e358'], 'Content-Length': ['75'], 
    'Date': ['Sat, 03 Apr 2021 20:26:25 GMT'], 'X-Amzn-Trace-Id': ['root=1-6068cf6f-2f2f61e418e94bf90ebcb57b;sampled=0'], 
    'Content-Type': ['application/json']}, 'HttpHeaders': {'Connection': 'keep-alive', 'Content-Length': '75', 
    'Content-Type': 'application/json', 'Date': 'Sat, 03 Apr 2021 20:26:25 GMT', 'X-Amz-Executed-Version': '$LATEST', 
    'x-amzn-Remapped-Content-Length': '0', 'x-amzn-RequestId': 'c59e6cdb-f51c-4897-b1d3-04cbead3e358', 
    'X-Amzn-Trace-Id': 'root=1-6068cf6f-2f2f61e418e94bf90ebcb57b;sampled=0'}, 'HttpStatusCode': 200}, 
    'SdkResponseMetadata': {'RequestId': 'c59e6cdb-f51c-4897-b1d3-04cbead3e358'}, 'StatusCode': 200}, ...]
    ```

    The "Payload" attribute contains the data we need to contatenate the clips together.
    All of that data will be concatenated into the `clips` variable that will be used to construct the
    MediaConvert Object.
    '''
    clips = []
    for item in event:
        payload = item.get('Payload')
        if not payload is None:
            clips.append(payload)

    sorted(clips, key=lambda clip: clip['position'])

    inputs = []
    for clip in clips:
        inputs.append(make_input(clip['name']))

    job_object = make_job(inputs)

    mediaconvert_client = boto3.client('mediaconvert')
    convertResponse = mediaconvert_client.create_job(**job_object)
    print(convertResponse)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(convertResponse, default=str)
    }
