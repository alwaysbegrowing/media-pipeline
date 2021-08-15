import json
import os
import uuid
from datetime import datetime
from googleapiclient.discovery import build


import boto3




def json_handler(item):
    if type(item) is datetime:
        return item.isoformat()
    else:
        return str(item)


def handler(event, context):
    print(event)
    yt_service = build('youtube', 'v3', developerKey='AIzaSyA_0LLkztJsoXrnYwsuH6OfTkmx5bFrkeM')
    videos = yt_service.videos().list(part='contentDetails, snippet', id='UCG8eMsXvCwGG6bszBwRUXmw').execute()
    print(videos)



handler(None, None)

