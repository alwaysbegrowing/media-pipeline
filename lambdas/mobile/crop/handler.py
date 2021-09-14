import os
import json

import boto3

from job_constructor import MCJob

OUT_BUCKET = os.getenv('OUT_BUCKET')
IN_BUCKET = os.getenv('IN_BUCKET')
QUEUE_ARN = os.getenv('QUEUE_ARN')
ROLE_ARN = os.getenv('ROLE_ARN')

'''
This is the data that is needed to start mediaconvert.
{
   {
  "ClipName": "clip_name",
  "Outputs": {
        "background": {
            "x": 100,
            "y": 100,
            "width": 100,
            "height": 100,
            "res_x": 100,
            "res_y": 100
        },
        'content': {...},
        'facecam': {...},
    }
}
'''


def handler(event, context):

    print(json.dumps(event))

    job_constructor = MCJob(QUEUE_ARN, ROLE_ARN)

    # get input from the event
    job_constructor.add_input(IN_BUCKET, event['ClipName'])

    outputs = event['Outputs']

    # add outputs to the job
    for output in outputs:
        crop = MCJob.create_crop(
            outputs[output]['x'], outputs[output]['y'], outputs[output]['width'], outputs[output]['height'])
        job_constructor.add_output(
            OUT_BUCKET, output, outputs[output]['res_x'], outputs[output]['res_y'], crop=crop)

    # create the job
    job = job_constructor.create()

    print(f'Constructed Job:')
    print(json.dumps(job, indent=4))

    mediaconvert_client = boto3.client(  # need endpoint url to start mediaconvert
        'mediaconvert', endpoint_url='https://lxlxpswfb.mediaconvert.us-east-1.amazonaws.com')
    mediaconvert_client.create_job(**job)

    background_file = f'{event["ClipName"]}background.mp4'
    content_file = f'{event["ClipName"]}content.mp4'
    facecam_file = f'{event["ClipName"]}facecam.mp4'

    return {
        'background_file': background_file,
        'content_file': content_file,
        'facecam_file': facecam_file
    }
