import json
import os
import uuid

import boto3
import streamlink


def handler(event, context):
    '''
    Here is what the request body will look like.
    {
        'clips': [{'start_time': 55, 'end_time': 90, 'name': 'clip12', 'position': 12}],
        'original_url': 'https://www.twitch.tv/videos/964350897',
    }

    The response body will be the state input body with the response
    from the request to create the state appended to the state input
    '''
    job = json.loads(event.get('body'))

    original_url = job.get('original_url')
    clips = job.get('clips')

    streams = streamlink.streams(original_url)
    best_stream = streams.get('best').url

    state = {
        'stream_manifest_url': best_stream,
        'clips': []
    }

    sfn = boto3.client('stepfunctions')

    for clip in clips: # this will be changed to add tasks
        data = {
            'end_time': clip.get('end_time'),
            'start_time': clip.get('start_time'),
            'stream_manifest_url': best_stream,
            'name': clip.get('name') + '.mp4',
            'position': clip.get('position')
        }
        state['clips'].append(data)

    resp = sfn.start_execution(
        stateMachineArn=os.getenv('STEPFUNCTION_ARN'),
        name=uuid.uuid4(),
        input=json.dumps(state)
    )

    state.update(resp)

    return {
        'statusCode': 200
        'headers': {
            'Content-Type': 'application/json'
        },
        body: json.dumps(state)
    }
        