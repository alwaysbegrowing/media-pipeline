import os
import json

import boto3

from job_constructor import MCJob

IN_BUCKET = os.getenv('INPUT_BUCKET')
QUEUE_ARN = os.getenv('QUEUE_ARN')
ROLE_ARN = os.getenv('ROLE_ARN')

'''
This is the data that is needed to start mediaconvert.
{
    'ClipName': 'clip_name',
    'Outputs': [
        {
            'bucket': 'bucket_name',
            'output_name': 'output_name',
            'x': 100,
            'y': 100,
            'width': 100,
            'height': 100,
            'res_x': 100,
            'res_y': 100
        },
    ]
}
'''


def handler(event, context):

    print(json.dumps(event))

    job_constructor = MCJob(QUEUE_ARN, ROLE_ARN)

    # get input from the event
    job_constructor.add_input(IN_BUCKET, event['ClipName'])

    # add outputs to the job
    for output in event['Outputs']:
        crop = MCJob.create_crop(
            output['x'], output['y'], output['width'], output['height'])
        job_constructor.add_output(
            output['bucket'], output['output_name'], output['res_x'], output['res_y'], crop=crop)

    # create the job
    job = job_constructor.create()

    print(f'Constructed Job:')
    print(json.dumps(job, indent=4))

    mediaconvert_client = boto3.client(  # need endpoint url to start mediaconvert
        'mediaconvert', endpoint_url='https://lxlxpswfb.mediaconvert.us-east-1.amazonaws.com')
    mediaconvert_client.create_job(**job)

    return {}
