import json
import os
import uuid
import boto3
from botocore.exceptions import ClientError

OUT_BUCKET = os.getenv('OUT_BUCKET')
QUEUE_ARN = os.getenv('QUEUE_ARN')
QUEUE_ROLE = os.getenv('QUEUE_ROLE')


def make_input(filename):
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


def make_job(inputs, task_token, requester_id):
    task_token1 = task_token[0:256]
    task_token2 = task_token[256:512]
    task_token3 = task_token[512:768]

    with open('job.json') as f:
        job_str = f.read()

    job_str = job_str.replace('**name_modifier**', 'basic-combiner')
    job_str = job_str.replace('**bucketname**', f'{OUT_BUCKET}/{requester_id}')
    job_str = job_str.replace('**task_token1**', task_token1)
    job_str = job_str.replace('**task_token2**', task_token2)
    job_str = job_str.replace('**task_token3**', task_token3)
    job_str = job_str.replace('**requester_id**', str(requester_id))
    job_str = job_str.replace('**bucket**', OUT_BUCKET)


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
    task_token = event['TaskToken']
    requester_id = event['requesterId']
    individual_clips = event['individualClips']
    sorted(individual_clips, key=lambda clip: clip['position'])





    inputs = []
    for clip in individual_clips:
        inputs.append(make_input(clip['file']))

    job_object = make_job(inputs, task_token, requester_id)

    mediaconvert_client = boto3.client(  # need endpoint url to start mediaconvert
        'mediaconvert', endpoint_url='https://lxlxpswfb.mediaconvert.us-east-1.amazonaws.com')
    mediaconvert_client.create_job(**job_object)

    return {}
