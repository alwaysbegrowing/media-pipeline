import os
import json

import boto3

IN_BUCKET = os.getenv('INPUT_BUCKET')

# This will be reused for cropping with various inputs

# construct the media convert job


def make_job(clip_name, input_bucket, output_bucket, x, y, w, h):
    job_string = ''

    with open('crop_job.json', 'r') as f:
        job_string = f.read()

    job_string = job_string.replace('"**x**"', str(x))
    job_string = job_string.replace('"**y**"', str(y))
    job_string = job_string.replace('"**w**"', str(w))
    job_string = job_string.replace('"**h**"', str(h))
    job_string = job_string.replace('"**input_bucket**"', input_bucket)
    job_string = job_string.replace('"**output_bucket**"', output_bucket)
    job_string = job_string.replace('"**filename**"', clip_name)

    return json.loads(job_string)


def handler(event, context):

    print(event)

    # get clip name
    clip_name = event['clip_name']
    # get output bucket
    output_bucket = event['output_bucket']
    # get x, y, h, w
    x = event['x']
    y = event['y']
    w = event['w']
    h = event['h']

    # make the job
    job = make_job(clip_name, IN_BUCKET, output_bucket, x, y, w, h)

    mediaconvert_client = boto3.client(  # need endpoint url to start mediaconvert
        'mediaconvert', endpoint_url='https://lxlxpswfb.mediaconvert.us-east-1.amazonaws.com')
    mediaconvert_client.create_job(**job)

    return {}
