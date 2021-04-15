import json
import os
import uuid
from datetime import datetime

import boto3
import streamlink

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
        'clips': [{'start_time': 55, 'end_time': 90, 'name': 'clip12', 'position': 12}],
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

    for clip in clips:  # this will be changed to add tasks
        name = clip.get('name')
        data = {
            'end_time': clip.get('end_time'),
            'start_time': clip.get('start_time'),
            'stream_manifest_url': best_stream,
            'name': f'{video_id}/{start_time}-{end_time}',
            'position': clip.get('position'),
            'render': render
        }
        state['clips'].append(data)

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
