import boto3
import json
# import ffmpy # how the heck do i import this!!
# import youtube_dl

# ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'})
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
    except ClientError as e:
        logging.error(e)
        return False
    return True


def handler(event, context):

    mediaconvert_client = boto3.client(
        'mediaconvert', endpoint_url=mediaconvert_endpoint)

    # get messages from API
    # download messages with timestamp
    # upload messages to s3 bucket
    # add s3 urls to job object

    # upload_file(file_name)

    s3Urls = ['s3://pillarclips/clip_11_im_baguette_2021-02-14T04:58:48Z.mp4',
              's3://pillarclips/clip_11_im_baguette_2021-02-14T04:58:48Z.mp4']
    job_object = buildObj(s3Urls)

    convertResponse = mediaconvert_client.create_job(**job_object)
    print(convertResponse)
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": event['body']
    }


