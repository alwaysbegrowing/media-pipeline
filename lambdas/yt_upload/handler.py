import base64
import json
import os
import uuid
from datetime import datetime

import s3fs
from youtube_upload.client import YoutubeUploader

from db import connect_to_db
from yt_secrets import get_yt_secrets

yt_secrets = get_yt_secrets()
YT_CLIENT_ID = yt_secrets['YT_CLIENT_ID']
YT_CLIENT_SECRET = yt_secrets['YT_CLIENT_SECRET']

def handler(event, context):
    print(event)
    os.chdir('/tmp')

    db = connect_to_db()
    search = {"twitch_id": "128675916"}

    yt_access_tokens = db['youtube_tokens'].find_one(search)
    access_token = yt_access_tokens['access_token']
    refresh_token = yt_access_tokens['refresh_token']

    uploader = YoutubeUploader(YT_CLIENT_ID, YT_CLIENT_SECRET)

    options = {
        "title" : "Example title", # The video title
        "description" : "Example description", # The video description
        "tags" : ["tag1", "tag2", "tag3"],
        "categoryId" : "22",
        "privacyStatus" : "private", # Video privacy. Can either be "public", "private", or "unlisted"
        "kids" : False, # Specifies if the Video if for kids or not. Defaults to False.
        "thumbnailLink" : "https://cdn.havecamerawilltravel.com/photographer/files/2020/01/youtube-logo-new-1068x510.jpg" # Optional. Specifies video thumbnail.
    }
    
    uploader.authenticate(access_token=access_token, refresh_token=refresh_token)
    
    # get s3 file path from event
    s3_file = event['file_path']

    # construct s3 fs
    s3 = s3fs.S3FileSystem(anon=False)

    video = s3.open(s3_file)

    try:
        # upload to youtube
        result = uploader.upload_stream(video, options)

        uploader.close()
        video.close()

        print(result)
        return result
    except Exception as e:
        print(e)
        return {'error': str(e)}






            



