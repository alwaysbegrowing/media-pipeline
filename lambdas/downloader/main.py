import os
import json

import boto3
import ffmpeg

def handler(event, context):
    '''
    This is what the event body is going to look like:
    {
        'stream_manifest_url': 'https://d2e2de1etea730.cloudfront.net/a359af50e593ba0523f2_syndicate_41548964492_1616754736/chunked/index-muted-NKKI82IMYD.m3u8',
        'start_time': 4230,
        'end_time': 4300,
        'name': 'clip12.mp4',
        'bucket': 'pillarclips'   
    }
    '''
    body = event.get('body')

    if body is None:
        raise AssertionError('Body is null.')

    job = json.loads(body)
    name = job.get('name')
    bucket = job.get('bucket') or 'pillarclips'

    stream_manifest_url = job.get('stream_manifest_url')

    input_stream = ffmpeg.input(stream_manifest_url)
    input_stream.trim(start=job.get('start_time'), end=job.get('end_time'))
    input_stream.output(name)
    input_stream.run()

    s3 = boto3.client('s3')
    s3.upload_file(name, job.get('bucket'), name)

    return {
        'statusCode': 200
    }
