import json
import os


def handler(event, context):
    '''
    Will take a list of clips and make a notification event out of them.
    '''

    os.getenv('BUCKET_DNS')

    clips = []
    for item in event:
        clip = item.get('Payload')
        if not clip is None:
            name = clip.get('name')
            clip['url'] = f'https://{BUCKET_DNS}/{name}'
            clips.append(clip)

    sorted(clips, key=lambda clip: clip['position'])

    body = {
        'clips': clips,
        'render': False
    }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, default=str)
    }
