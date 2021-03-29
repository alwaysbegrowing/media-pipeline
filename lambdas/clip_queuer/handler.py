import os
import json

import boto3

import streamlink

def handler(event, context):
    '''
    Here is what the request body will look like.
    {
        'clips': [{'start_time': 55, 'end_time': 90, 'name': 'clip12'}],
        'original_url': 'https://www.twitch.tv/videos/964350897',
    }
    '''
    job = json.loads(event.get('body'))

    original_url = job.get('original_url')
    clips = job.get('clips')

    streams = streamlink.streams(original_url)
    best_stream = streams.get('best').url

    sqs = boto3.client('sqs')

    for clip in clips:
        data = {
            'end_time': clip.get('end_time'),
            'start_time': clip.get('start_time'),
            'stream_manifest_url': best_stream,
            'name': clip.get('name') + '.mp4',
            'bucket': os.getenv('BUCKET')
        }
        data_str = json.dumps(data)
        resp = client.send_message(
            QueueUrl=os.getenv('DOWNLOAD_QUEUE'),
            MessageBody=data_str
        )

    return {
        'statusCode': 200
        'headers': {
            'Content-Type': 'application/json'
        },
        body: '{}'
    }
        