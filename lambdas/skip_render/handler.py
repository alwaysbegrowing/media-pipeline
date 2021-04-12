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
        clip = item.get('Payload')
        if not clip is None:
            name = clip.get('name')
            clip['url'] = f'https://{BUCKET_DNS}/{name}'
            clips.append(clip)

    sorted(clips, key=lambda clip: clip['position'])

    sns = boto3.client('sns')
    resp = sns.publish(
        TopicArn=SNS_TOPIC,
        Message=json.dumps(clips),
        Subject=f'{len(clips)} clips were downloaded.'
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(resp, default=str)
    }
