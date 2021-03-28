import json
import logging
import boto3
import os
from botocore.exceptions import ClientError

# import ffmpy # how the heck do i import this and package with the lambda!!
# import youtube_dl

# ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'})


BUCKET = os.getenv('BUCKET')


def makeInput(file):
    return {
        "AudioSelectors": {
            "Audio Selector 1": {
                "Offset": 0,
                "DefaultSelection": "DEFAULT",
                "ProgramSelection": 1
            }
        },
        "VideoSelector": {
            "ColorSpace": "FOLLOW",
            "Rotate": "DEGREE_0",
            "AlphaBehavior": "DISCARD"
        },
        "FilterEnable": "AUTO",
        "PsiControl": "USE_PSI",
        "FilterStrength": 0,
        "DeblockFilter": "DISABLED",
        "DenoiseFilter": "DISABLED",
        "InputScanType": "AUTO",
        "TimecodeSource": "ZEROBASED",
        "FileInput": file
    }


mediaconvert_endpoint = 'https://lxlxpswfb.mediaconvert.us-east-1.amazonaws.com'


def buildObj(s3Urls):
    with open("job.json", "r") as jsonfile:
        job_object = json.load(jsonfile)

    for url in s3Urls:
        job_object['Settings']['Inputs'].append(makeInput(url))
    return job_object


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
        return response
    except ClientError as e:
        logging.error(e)
        return False
    return True


def download_clips(timestamps):
    # add logic to use youtube-dl and ffmpeg to download the clips
    # return an array with all the file paths
    return []

def handler(event, context):

    # example body 
    # {
    #     "clips": [{"startTime": 60, "endTime": 90, "videoId": 964746682}]
    # }
    timestamps = event['body'].clips

    clip_local_file_paths = download_clips(timestamps)
    for file_name in clip_local_file_paths:
        upload_file(file_name, BUCKET)

    job_object = buildObj(clip_local_file_paths)

    mediaconvert_client = boto3.client(
        'mediaconvert', endpoint_url=mediaconvert_endpoint)
    convertResponse = mediaconvert_client.create_job(**job_object)
    print(convertResponse)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": convertResponse
    }
