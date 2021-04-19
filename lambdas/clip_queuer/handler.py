import json
import os
import uuid
from datetime import datetime

import boto3
import streamlink

from clip_lib import get_ccc_start_end_times
from lib import get_secret, json_handler


STATE_MACHINE_ARN = os.getenv('STEPFUNCTION_ARN')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET_ARN = os.getenv('TWITCH_CLIENT_SECRET_ARN')
TWITCH_CLIENT_SECRET = get_secret(TWITCH_CLIENT_SECRET_ARN)


def handler(event, context):
    '''
    Here is what the request body will look like.
    {
        'clips': [{'start_time': 55, 'end_time': 90}, {"clip_url": "https://www.twitch.tv/smii7y/clip/NeighborlyBombasticPancakeTTours-YnJN7ray0zhct_v5"}],
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

    for clip in clips:
        stream_manifest_url = best_stream
        start_time = clip.get('start_time', 0)
        end_time = clip.get('end_time', 0)
        name = f'{video_id}-{start_time}-{end_time}'
        ccc = False
        # if clip is a CCC
        # rather than a generated clip
        if clip.get('clip_url'):
            clip_url = clip.get('clip_url')
            clip_slug = clip_url.split('/')[-1]

            start_time, end_time = get_ccc_start_end_times(twitch_client_id=TWITCH_CLIENT_ID,
                                                           twitch_client_secret=TWITCH_CLIENT_SECRET,
                                                           clip_slug=clip_slug)

            name = f'{video_id}-{clip_slug}'
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
