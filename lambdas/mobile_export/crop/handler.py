import os
import json

import boto3

from job_constructor import MediaConvertJobHandler

OUT_BUCKET = os.getenv('OUT_BUCKET')
IN_BUCKET = os.getenv('IN_BUCKET')
QUEUE_ARN = os.getenv('MEDIACONVERT_ARN')
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

    dry_run = event.get('DryRun', False)

    if dry_run:
        print('Dry run, not actually cropping')
        OUT_BUCKET = 'test'
        IN_BUCKET = 'test'
        QUEUE_ARN = 'test'
        ROLE_ARN = 'test'

    print(json.dumps(event))

    job_constructor = MediaConvertJobHandler(QUEUE_ARN, ROLE_ARN)
    job_constructor.add_task_token(event['TaskToken'])

    # get input from the event
    job_constructor.add_input(event['ClipName'])

    outputs = event['Outputs']

    # add outputs to the job
    for output in outputs:
        res_x = outputs[output].get('res_x')
        res_y = outputs[output].get('res_y')

        if not res_x or not res_y:
            res_x = outputs[output]['resX']
            res_y = outputs[output]['resY']

        crop = MediaConvertJobHandler.create_crop(
            outputs[output]['x'],
            outputs[output]['y'],
            outputs[output]['width'],
            outputs[output]['height'])
        job_constructor.add_output(
            OUT_BUCKET,
            output,
            outputs[output]['res_x'],
            outputs[output]['res_y'],
            crop=crop)

    # create the job
    job = job_constructor.create()

    print(f'Constructed Job:')
    print(json.dumps(job))

    if not dry_run:
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
