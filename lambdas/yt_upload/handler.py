import os
import s3fs
from youtube_upload.client import YoutubeUploader

from db import connect_to_db
from yt_secrets import get_yt_secrets

yt_client_id, yt_client_secret = get_yt_secrets()


def handler(event, context):
    print(event)
    os.chdir('/tmp')

    db = connect_to_db()
    dry_run = event['data'].get('dryRun')
    twitch_id = event['user']['id']
    display_name = event['user']['display_name']
    s3_file = event['mediaConvertResult']['outputFilePath']

    search = {"twitch_id": twitch_id}

    yt_access_tokens = db['youtube_tokens'].find_one(search)
    access_token = yt_access_tokens['access_token']
    refresh_token = yt_access_tokens['refresh_token']

    uploader = YoutubeUploader(yt_client_id, yt_client_secret)

    options = {
        "title": f'{display_name} - Highlights',  # The video title
        "description": f'Hey {display_name} - I made this compliation of your latest stream, let me know what you think!',
        "categoryId": "20",
        # Video privacy. Can either be "public", "private", or "unlisted"
        "privacyStatus": "private",
        # Specifies if the Video if for kids or not. Defaults to False.
        "kids": False,
    }

    uploader.authenticate(access_token=access_token,
                          refresh_token=refresh_token)

    # construct s3 fs
    s3 = s3fs.S3FileSystem(anon=False)

    video = s3.open(s3_file)
    if (dry_run):
        return {"edit_url": "https://studio.youtube.com/video/JQZ6Bv12fUw/edit"}
    try:
        # upload to youtube
        result = uploader.upload_stream(video, options)
        print(result)
        uploader.close()
        video.close()

        video_id = result[0]['id']
        edit_url = f'https://studio.youtube.com/video/{video_id}/edit'
        return {"edit_url": edit_url}
    except Exception as e:
        print(e)
        return {'error': str(e)}
