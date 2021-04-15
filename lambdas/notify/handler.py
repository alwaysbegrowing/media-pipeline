import json
import os
import re

import boto3

BUCKET_DNS = os.getenv('BUCKET_DNS')


def handler(event, context):
    '''
    Will take the event and transform it into a notification for SES.
    Will take S3 notifications and manual invocation from "skip_render".
    Here an an example of the S3 notification event invocation:
    ```
    {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "2021-04-13T16:37:25.401Z",
                "eventName": "ObjectCreated:CompleteMultipartUpload",
                "userIdentity": {
                    "principalId": "AWS:AROAYMSL2M6TO7VFAQ4RM:EmeSession_dc715bb615de7955cb45c69a0419b4ed"
                },
                "requestParameters": {
                    "sourceIPAddress": "172.31.80.10"
                },
                "responseElements": {
                    "x-amz-request-id": "FGCCXK04H91BZ49G",
                    "x-amz-id-2": "NAdivVjM6kA7U/aiZjQZFkpeHD9K11PxHd9IQF2nlqSPgvU0uacKom9WTs44V9cUfpAzh2Q7OYrPTnym/CrS8oQ+E3Q/6Wwe"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "ZDljMjAyNGMtMjczZS00ODBhLTk1YjktMGQxMGIxNjY3Nzcx",
                    "bucket": {
                        "name": "renderlambdastack-combinedclips9275ae0a-exc6csik1g96",
                        "ownerIdentity": {
                            "principalId": "AK7KQUDP8IB11"
                        },
                        "arn": "arn:aws:s3:::renderlambdastack-combinedclips9275ae0a-exc6csik1g96"
                    },
                    "object": {
                        "key": "964350897-clip1final-render.mp4",
                        "size": 190323650,
                        "eTag": "84893e6aec730542232ab9d8eee7a864-8",
                        "sequencer": "006075C8C76192A3D0"
                    }
                }
            }
        ]
    }
    ```
    '''

    records = event.get('Records')
    body = {}

    if records != None:
        # Event is an S3 Notification
        body['render'] = True
        body['clips'] = []

        name = records[0]['s3']['object'].get('key')
        body['video'] = f'https://{BUCKET_DNS}/{name}'
    else:
        body = event

    print(body)
    '''
    Here is what the Body will look like:
    ```
    {
        'clips': [],
        'video': 'https://renderlambdastack-combinedclips9275ae0a-exc6csik1g96.s3.amazonaws.com/964350897-clip1final-render.mp4',
        'render': true
    }
    ```
    If "clips" is empty and "render" is true, "video" should be populated with a link to the final rendered video.   

    If "clips" is populated and "render" is true, "video" should be null. Here is another example:
    ```
    {
        "clips": [
            {
                "position": 1,
                "name": "964350897-clip1.mkv",
                "url": "https://renderlambdastack-individualclips96d9129c-1m2rui0jjqo4r.s3.amazonaws.com/964350897-clip1.mkv"
            },
            {
                "position": 2,
                "name": "964350897-clip2.mkv",
                "url": "https://renderlambdastack-individualclips96d9129c-1m2rui0jjqo4r.s3.amazonaws.com/964350897-clip2.mkv"
            },
            {
                "position": 3,
                "name": "964350897-clip3.mkv",
                "url": "https://renderlambdastack-individualclips96d9129c-1m2rui0jjqo4r.s3.amazonaws.com/964350897-clip3.mkv"
            }
        ],
        "render": false,
        "video": null
    } 
    ```
    '''

    # do notification stuffs

    return {
        'statusCode': 200
    }