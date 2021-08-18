import json
import os
import uuid
from datetime import datetime
import boto3
import base64
from botocore.exceptions import ClientError
from db import connect_to_db



import boto3

cached_yt_secrets = None

def get_yt_secrets():
    global cached_yt_secrets
    yt_secret_name = "YT_CREDENTIALS"

    if (not cached_yt_secrets):
        session = boto3.session.Session()
        secret_client = session.client(
            service_name='secretsmanager'
        )
        cached_yt_secrets = secret_client.get_secret_value(
                SecretId=yt_secret_name)['SecretString']
    return json.loads(cached_yt_secrets)




def handler(event, context):
    print(event)
    print(get_yt_secrets())

    db = connect_to_db()
    search = {"twitch_id": "128675916"}

    result = db['youtube_tokens'].find_one(search)
    print(result)
    return result







            



