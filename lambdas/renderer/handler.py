import json
import os
import uuid
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


def make_job(inputs, task_token):
    task_token1 = task_token[0:256]
    task_token2 = task_token[256:512]
    task_token3 = task_token[512:768]

    with open('job.json') as f:
        job_str = f.read()

    job_str = job_str.replace('**name_modifier**', str(uuid.uuid4()))
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
    Check renderEvent.json to see structure of event
    '''

    print(event)
    clips = []
    task_token = event['TaskToken']

    for item in event['Input']:
        payload = item.get('Payload')
        if not payload is None:
            clips.append(payload)

    clip = clips[0]

    sorted(clips, key=lambda clip: clip['position'])

    inputs = []
    for clip in clips:
        inputs.append(make_input(clip['name']))

    job_object = make_job(inputs, task_token)

    mediaconvert_client = boto3.client(  # need endpoint url to start mediaconvert
        'mediaconvert', endpoint_url='https://lxlxpswfb.mediaconvert.us-east-1.amazonaws.com')
    mediaconvert_client.create_job(**job_object)

    return {}
