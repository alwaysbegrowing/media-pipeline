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
        'render': True
    }
    '''
    os.chdir('/tmp')
    job = event
    name = job.get('name')
    download_name = f'{name}.mkv'
    start_time = str(job.get('start_time'))
    duration = str(job.get('end_time') - job.get('start_time'))

    render = job.get('render', True)
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

    s3_name = download_name.replace('-', '/', 1)

    if not job.get('dry_run'):
        print('Dry run, skipping upload.')
        s3 = boto3.client('s3')
        s3.upload_file(download_name, BUCKET, s3_name)

    os.remove(download_name)
    return {
        'position': job.get('position'),
        'name': s3_name,
        'render': render
    }

if __name__=='__main__':
    import twitch
    import streamlink
    # This is for testing.
    # Will run if you build Dockerfile.test
    event = {}
    context = {}

    print('Generating test data...')
    
    with open('downloadEvent.json') as f:
        event = json.loads(f.read())

    helix = twitch.Helix(os.getenv('TWITCH_CLIENT_ID'), os.getenv('TWITCH_CLIENT_SECRET'))

    video_id = None

    while video_id is None:
        top_game = helix.top_game()
        videos = top_game.videos()
        # videos is a generator.
        # this is the easiest way to get a video id
        for video in videos:
            video_id = video.id
            break

    video_url = f'https://twitch.tv/videos/{video_id}'

    streams = streamlink.streams(video_url)
    event['stream_manifest_url'] = streams.get('best').url
    event['name'] = f'{video_id}-test'
    event['dry_run'] = True

    print('Done. Test data:')
    print(json.dumps(event, indent=4))
    handler(event, context)
