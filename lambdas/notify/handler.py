import json
import os
import re

import boto3


def handler(event, context):
    '''
    This will take the event from either the render lambda or the skip lambda and 
    put it into a format for the notification lambda to read off of either an SQS or 
    SNS queue.
    '''
    attributes = {}

    render = event.get('render')

    if render:
        video_url = event.get('videoURL')
        url_numbers = re.findall(r'\d+-', video_url)

        attributes['VideoId'] = {
            'Type': 'String',
            'Value': event.get('videoId')
        }

        attributes['Video'] = {
            'Type': 'String',
            'Value':}

    TOPIC_ARN = os.getenv('TOPIC_ARN')

    sns = boto3.client('sns')
