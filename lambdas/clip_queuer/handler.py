import json
import os
import uuid
from datetime import datetime

import boto3
import streamlink



def handler(event, context):
    print("event", event)
    '''
    Here is what the request body will look like.
    {
        'clips': [{'startTime': 55, 'endTime': 90}],
        'videoId': '964350897',
        'render': true,
    }
    '''



    prefix = 'https://twitch.tv/videos/'

    video_id = event.get('videoId')

    original_url = f'{prefix}{video_id}'

    clips = event.get('clips')

    streams = streamlink.streams(original_url)
    best_stream = streams.get('best').url
    render = event.get('render', True)

    state = {
        'render': render,
        'stream_manifest_url': best_stream,
        'clips': []
    }


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


    return state
