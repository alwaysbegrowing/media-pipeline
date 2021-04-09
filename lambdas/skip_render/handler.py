import json
import os

import boto3


def handler(event, context):
    '''
    Will take a list of clips and make a notification event out of them.
    '''

    BUCKET = os.getenv('BUCKET')
    SNS_TOPIC = os.getenv('TOPIC_ARN')
    BUCKET_DNS = os.getenv('BUCKET_DNS')

    clips = []
    for item in event:
        payload = item.get('Payload')
        if not payload is None:
            name = clip.get('name')
            payload['url'] = f'https://{BUCKET_DNS}/{name}'
            clips.append(payload)

    sorted(clips, key=lambda clip: clip['position'])

    sns = boto3.client('sns')
    resp = sns.publish(
        TopicArn=SNS_TOPIC,
        Message=json.dumps(clips),
        Subject=f'{len(clip_links)} clips were downloaded.', ,
        MessageStructure='json'
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(resp, default=str)
    }
