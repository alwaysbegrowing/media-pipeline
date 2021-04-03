import os
import json
import uuid

import boto3
from ffmpy import FFmpeg

from lib import seconds_to_ffmpeg_time


def handler(event, context):
    '''
    This is what the event body is going to look like:
    {
        'stream_manifest_url': 'https://d2e2de1etea730.cloudfront.net/a359af50e593ba0523f2_syndicate_41548964492_1616754736/chunked/index-muted-NKKI82IMYD.m3u8',
        'start_time': 4230,
        'end_time': 4300,
        'name': 'clip12',
        'position': 12
    }
    '''
    os.chdir('/tmp')
    job = event
    name = job.get('name')
    download_name = f'{uuid.uuid4()}-{name}.mkv'
    bucket = os.getenv('BUCKET')
    start_time = seconds_to_ffmpeg_time(job.get('start_time'))
    duration = str(job.get('end_time') - job.get('start_time'))

    stream_manifest_url = job.get('stream_manifest_url')

    ffmpeg_inputs = {
        stream_manifest_url: ['-ss', start_time]
    }

    ffmpeg_outputs = {
        download_name:  ['-t', duration, '-y', '-c', 'copy']
    }
    #ffmpeg_global_options = ['-hide_banner', '-loglevel', 'panic']

    ffmpeg_global_options = []

    ffmpeg = FFmpeg(inputs=ffmpeg_inputs, outputs=ffmpeg_outputs,
                    global_options=ffmpeg_global_options)
    ffmpeg.run()

    s3 = boto3.client('s3')
    s3.upload_file(download_name, bucket, download_name)
    os.remove(download_name)
    return {
        'position': job.get('position'),
        'name': download_name
    }
