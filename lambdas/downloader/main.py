import os
import json

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
        'render': True
    }
    '''
    os.chdir('/tmp')
    job = event
    name = job.get('name')
    download_name = f'{name}.mkv'
    start_time = str(job.get('start_time'))
    duration = str(job.get('end_time') - job.get('start_time'))

    # local_download_name is the name that FFMPEG will use to temporarily process the object
    # "job" is the JSON used to process the download
    print(json.dumps({'local_download_name': download_name, 'job': job}))

    render = job.get('render', True)
    stream_manifest_url = job.get('stream_manifest_url')

    ffmpeg_inputs = {
        stream_manifest_url: ['-ss', start_time]
    }

    ffmpeg_outputs = {
        download_name:  ['-t', duration, '-y', '-c', 'copy']
    }

    ffmpeg_global_options = []

    ffmpeg = FFmpeg(inputs=ffmpeg_inputs, outputs=ffmpeg_outputs,
                    global_options=ffmpeg_global_options)

    print(json.dumps({'ffmpeg_command_used': ffmpeg.cmd}))

    ffmpeg.run()

    s3_name = download_name.replace('-', '/', 1)

    if not job.get('dry_run'):
        print('Uploading....')
        s3 = boto3.client('s3')
        s3.upload_file(download_name, BUCKET, s3_name)
    else:
        print('Dry run, skipping upload.')

    os.remove(download_name)

    body = {
        'position': job.get('position'),
        'name': s3_name,
        'render': render,
        'bucket': BUCKET
    }

    # this part of the object that will be passed either to the 
    # renderer or passed to the notification lambda
    print(json.dumps({'render_job_metadata':body}))
    return body
