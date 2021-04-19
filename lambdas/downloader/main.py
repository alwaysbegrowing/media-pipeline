import os
import json
import uuid

import boto3
from ffmpy import FFmpeg

BUCKET = os.getenv('BUCKET')


def handler(event, context):
    '''
    This is what the event body is going to look like:
    {
        'stream_manifest_url': 'https://d2e2de1etea730.cloudfront.net/a359af50e593ba0523f2_syndicate_41548964492_1616754736/chunked/index-muted-NKKI82IMYD.m3u8',
        'start_time': 4230,
        'end_time': 4300,
        'name': 'clip12',
        'position': 12,
        'render': true,
        'ccc': false
    }
    '''
    os.chdir('/tmp')
    name = event.get('name')
    download_name = f'{name}.mkv'

    render = event.get('render', True)
    stream_manifest_url = event.get('stream_manifest_url')

    start_time = str(event.get('start_time'))
    duration = str(event.get('end_time') - event.get('start_time'))
    ffmpeg_inputs = {
        stream_manifest_url: ['-ss', start_time]
    }

    ffmpeg_outputs = {
        download_name:  ['-t', duration, '-y', '-c', 'copy']
    }

    ffmpeg = FFmpeg(inputs=ffmpeg_inputs, outputs=ffmpeg_outputs)
    ffmpeg.run()

    s3_name = download_name.replace('-', '/', 1)

    s3 = boto3.client('s3')
    s3.upload_file(download_name, BUCKET, s3_name)
    os.remove(download_name)
    return {
        'position': event.get('position'),
        'name': s3_name,
        'render': render
    }
