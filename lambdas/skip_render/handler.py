import json
import os

import boto3


def handler(event, context):
    '''
    Will take a list of clips and make a notification event out of them.
    '''

    BUCKET_DNS = os.getenv('BUCKET_DNS')

    clips = []
    for item in event:
        clip = item.get('Payload')
        if not clip is None:
            name = clip.get('name')
            position = clip.get('position')
            new_clip = {
                'url': f'https://{BUCKET_DNS}/{name}',
                'name': name,
                'position': position
            }
            clips.append(new_clip)

    sorted(clips, key=lambda clip: clip['position'])

    print(clips)

    body = {
        'clips': clips,
        'render': False,
        'video': None
    }

    payload = json.dumps(body).encode()

    lambda_ = boto3.client('lambda')
    LAMBDA_ARN = os.getenv('LAMBDA_ARN')
    resp = lambda_.invoke(
        FunctionName=LAMBDA_ARN,
        Payload=payload,
        InvocationType='Event'
    )

    body.update(resp)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=str)
    }
