from email_templates import S3Success, FailureMessage, YoutubeSuccess
from utils import s3_to_http
import os
import boto3

FROM_EMAIL = os.getenv('FROM_EMAIL')
email_client = boto3.client('ses')


def handler(event, context):
    s3_url = event['mediaConvertResult']['outputFilePath']
    request_email = event['user']['email']
    display_name = event['user']['display_name']
    youtube_url = event.get('UploadToYoutubeResult', {}).get('youtubeData', {}).get('edit_url')
    compilation_file_url = s3_to_http(s3_url)

    if (youtube_url):
        message = YoutubeSuccess(display_name, youtube_url, compilation_file_url).message

    elif (s3_url):
        message = S3Success(display_name, compilation_file_url).message

    result = email_client.send_email(
        Source=FROM_EMAIL,
        Destination={
            'BccAddresses': [
                request_email,
            ]
        },
        Message=message
    )
    print(result)

    return {"message": message}
