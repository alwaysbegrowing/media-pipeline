import os

import boto3
from dbclient import DBClient
import twitch

from lib import get_secret

COMBINED_BUCKET_DNS = os.getenv('COMBINED_BUCKET_DNS')
INDIVIDUAL_BUCKET_DNS = os.getenv('INDIVIDUAL_BUCKET_DNS')
# FROM_EMAIL = os.getenv('FROM_EMAIL') # pro
FROM_EMAIL = 'chandler@chand1012.dev'
MONGODB_CONNECT_STR = get_secret(os.getenv('MONGODB_URI_SECRET_ARN'))
MONGODB_DBNAME = os.getenv('DB_NAME')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = get_secret(os.getenv('TWITCH_CLIENT_SECRET_ARN'))
SENDGRID_API_KEY = get_secret(os.getenv('SENDGRID_API_KEY_SECRET'))

def handler(event, context):
    '''
    Will take the event and transform it into a notification for SendGrid.
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

    body = {}

    # if triggered by S3
    if type(event) is dict:
        records = event.get('Records')
        for record in records:
            if record.get('eventSource') == 'aws:s3':
                # Event is an S3 Notification
                name = records[0]['s3']['object'].get('key')
                video = f'https://{COMBINED_BUCKET_DNS}/{name}'
                body = {
                    'render': True,
                    'clips': [],
                    'video': video
                }
    # if triggered by state machine
    elif type(event) is list:
        clips = []
        for item in event:
            clip = item.get('Payload')
            if clip:
                name = clip.get('name')
                position = clip.get('position')
                new_clip = {
                    'url': f'https://{INDIVIDUAL_BUCKET_DNS}/{name}',
                    'name': name,
                    'position': position
                }
                clips.append(new_clip)

        sorted(clips, key=lambda clip: clip['position'])

        body = {
            'clips': clips,
            'render': False,
            'video': None
        }

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

    dbclient = DBClient(db_name=MONGODB_DBNAME, connect_str=MONGODB_CONNECT_STR)
    helix = twitch.Helix(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)

    twitch_video_id = ''

    video_links = ''

    if body['clips'] != []:
        print('Input is clips.')
        clip = body['clips'][0]
        name = clip['name'].split('-')[0]
        twitch_video_id = name.split('/')[0]
        video_links = '<table><caption> Your Pillar Videos </caption>'
        for clip in body['clips']:
            video_links += f'<tr><td>{clip["name"]}</td><td>{clip["url"]}</td></tr>'
        video_links += '</table>'

    else:
        print('Input is video.')
        name = body['video'].split('/')[-1]
        twitch_video_id = name.split('-')[0]
        video_links = body['video']

    video = helix.video(twitch_video_id)

    user_twitch_id = video.user.id

    user = dbclient.get_user_by_twitch_id(user_twitch_id)

    email = user['email']
    name = user['display_name']
    
    email_client = boto3.client('ses')

    html = f'''
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
  <meta http-equiv="Content-Type" content="text/html charset=UTF-8" />
  <head>
  </head>
  <body>
  {name}, <br>
  Here are your Pillar videos: <br>
  
  {video_links}
  <br>
  Thanks for using Pillar! <br>
  If you'd like to leave feedback, let us know how your experience was (any bugs, questions, etc? ) by replying to the 2 minute survey we will send you soon. <br>
  See you soon, <br>
  The Pillar Team
      </body>
</html>
    '''

    email_client.send_email(
        Source=FROM_EMAIL,
        Destination={
            'BccAddresses': [
                email,
            ]
        },
        Message={
            'Subject': {
                'Data': 'Your PillarGG Job is Ready!'
            },
            'Body': {
            #     'Text': {
            #         'Data': str(body),
            #    }
                'Html': {
                    'Data': html
                }
            }
        }
    )

    return {}
