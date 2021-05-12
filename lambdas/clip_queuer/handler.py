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

    position = 1

    for clip in clips:  # this will be changed to add tasks
        start_time = clip.get('start_time')
        end_time = clip.get('end_time')
        if start_time is None:
            start_time = clip.get('startTime')
        if end_time is None:
            end_time = clip.get('endTime')
        data = {
            'end_time': end_time,
            'start_time': start_time,
            'stream_manifest_url': best_stream,
            'name': f'{video_id}-{start_time}-{end_time}',
            'position': position,
            'render': render
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
            'Content-Type': 'application/json',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            'Access-Control-Allow-Origin': '*',
            
        },
        'body': json.dumps(state, default=json_handler)
    }
