import json
import os
import uuid
from datetime import datetime

import boto3
import streamlink
from youtube_dl import YoutubeDL

STATE_MACHINE_ARN = os.getenv('STEPFUNCTION_ARN')


def json_handler(item):
    if type(item) is datetime:
        return item.isoformat()
    else:
        return str(item)


def handler(event, context):
    '''
    Here is what the request body will look like.
    {
        'clips': [{'start_time': 55, 'end_time': 90}, {"highlight_url": "https://www.twitch.tv/smii7y/clip/NeighborlyBombasticPancakeTTours-YnJN7ray0zhct_v5"}],
        'videoId': '964350897',
        'render': true
    }

    The response body will be the state input body with the response
    from the request to create the state machine appended to the state input
    '''
    job = json.loads(event.get('body'))

    prefix = 'https://twitch.tv/videos/'

    video_id = job.get('videoId')

    original_url = f'{prefix}{video_id}'

    clips = job.get('clips')

    streams = streamlink.streams(original_url)
    best_stream = streams.get('best').url
    render = job.get('render', True)

    state = {
        'render': render,
        'stream_manifest_url': best_stream,
        'clips': []
    }

    sfn = boto3.client('stepfunctions')

    position = 1

    for clip in clips:  # this will be changed to add tasks
        stream_manifest_url = best_stream
        start_time = clip.get('start_time', 0)
        end_time = clip.get('end_time', 0)
        name = f'{video_id}-{start_time}-{end_time}'
        ccc = False
        # if clip is a CCC
        # rather than a generated clip
        if clip.get('highlight_url'):
            highlight_url = clip.get('highlight_url')
            ytdl_options = {
                'format': 'best',  # format for the video
                'forceurl': True
            }

            with YoutubeDL(ytdl_options) as ytdl:
                # we are using YouTube DL because streamlink doesn't always
                # work when its a clip rather than a livestream
                info_dict = ytdl.extract_info(highlight_url, download=False)
                stream_manifest_url = info_dict.get('url')  # get the clip link

            clip_name = highlight_url.split('/')[-1]
            name = f'{video_id}-{clip_name}'
            ccc = True

        data = {
            'end_time': end_time,
            'start_time': start_time,
            'stream_manifest_url': stream_manifest_url,
            'name': name,
            'position': position,
            'render': render,
            'ccc': ccc
        }
        state['clips'].append(data)
        position += 1

    resp = sfn.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=str(uuid.uuid4()),
        input=json.dumps(state, default=json_handler)
    )

    state.update(resp)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(state, default=json_handler)
    }
