import os
import uuid

import boto3
import streamlink

from ffmpy import FFmpeg

BUCKET = os.getenv('BUCKET')


def get_stream_manifest_url(video_id):
    prefix = 'https://twitch.tv/videos/'
    original_url = f'{prefix}{video_id}'
    streams = streamlink.streams(original_url)
    return streams.get('best').url

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
    
    clip = event['clip']
    video_id = event['videoId']
    clip_index = event['index']
    download_name = f'{uuid.uuid4()}.mkv'
    start_time = clip['startTime']
    end_time = clip['endTime']
    duration = str(end_time - start_time)
    stream_manifest_url = get_stream_manifest_url(video_id)

    ffmpeg_inputs = {
        stream_manifest_url: ['-ss', str(start_time)]
    }

    ffmpeg_outputs = {
        download_name:  ['-t', duration, '-y', '-c', 'copy']
    }

    ffmpeg_global_options = []

    ffmpeg = FFmpeg(inputs=ffmpeg_inputs, outputs=ffmpeg_outputs,
                    global_options=ffmpeg_global_options)
    ffmpeg.run()


    if not event.get('dry_run'):
        print('Uploading....')
        s3 = boto3.client('s3')
        s3.upload_file(download_name, BUCKET, download_name)
    else:
        print('Dry run, skipping upload.')

    os.remove(download_name)
    return {
        'position': clip_index,
        'file': f's3://{BUCKET}/{download_name}',
        'render': True
    }
