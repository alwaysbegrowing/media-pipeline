import json
import os
import uuid
from datetime import datetime
import boto3
import base64
from botocore.exceptions import ClientError
from db import connect_to_db
from youtube_upload.client import YoutubeUploader





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
    os.chdir('/tmp')

    db = connect_to_db()
    search = {"twitch_id": "128675916"}
    yt_secrets = get_yt_secrets()
    YT_CLIENT_ID = yt_secrets['YT_CLIENT_ID']
    YT_CLIENT_SECRET = yt_secrets['YT_CLIENT_SECRET']


    yt_access_tokens = db['youtube_tokens'].find_one(search)
    access_token = yt_access_tokens['access_token']
    refresh_token = yt_access_tokens['refresh_token']

    uploader = YoutubeUploader(YT_CLIENT_ID,YT_CLIENT_SECRET)

    options = {
    "title" : "Example title", # The video title
    "description" : "Example description", # The video description
    "tags" : ["tag1", "tag2", "tag3"],
    "categoryId" : "22",
    "privacyStatus" : "private", # Video privacy. Can either be "public", "private", or "unlisted"
    "kids" : False, # Specifies if the Video if for kids or not. Defaults to False.
    "thumbnailLink" : "https://cdn.havecamerawilltravel.com/photographer/files/2020/01/youtube-logo-new-1068x510.jpg" # Optional. Specifies video thumbnail.
    }
    file_path = "https://qa-render-combinedclips9275ae0a-13myjw544jfv0.s3.amazonaws.com/128675916/ea534c46-68f8-4b78-a984-c61e7d242fc9-basic-combiner.mp4"
    uploader.authenticate(access_token=access_token, refresh_token=refresh_token)
    result= uploader.upload(file_path, options)

    print(result)
    return result







            



