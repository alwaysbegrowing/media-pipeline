
import os

import boto3

from email_templates import FailureMessage, S3Success, YoutubeSuccess
from get_aws_secret import get_aws_secret
from utils import s3_to_http, send_log_to_slack_channel

FROM_EMAIL = os.getenv('FROM_EMAIL')
email_client = boto3.client('ses')


def handler(event, context):
    mediaConvertResults = event.get('mediaConvertResult', {})
    s3_url = mediaConvertResults.get('outputFilePath')

    request_email = event['user']['email']
    display_name = event['user']['display_name']

    error = event.get('Error', {})
    error_message = error.get('Cause')
    error_name = error.get('Error')

    youtube_url = event.get(
        'UploadToYoutubeResult',
        {}).get(
        'youtubeData',
        {}).get('edit_url')

    if s3_url:
        compilation_file_url = s3_to_http(s3_url)

    if youtube_url:
        message = YoutubeSuccess(
            display_name,
            youtube_url,
            compilation_file_url).message

    elif s3_url:
        message = S3Success(display_name, compilation_file_url).message

    if error:
        send_log_to_slack_channel(display_name, request_email,
                                  error_name, error_message)
        message = FailureMessage(display_name, error_name)

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
