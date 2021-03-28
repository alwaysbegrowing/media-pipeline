import json
import boto3
# import ffmpy # how the heck do i import this!!

def handler(event, context):

    # get messages from API
    # download messages with timestamp
    # upload messages to s3 bucket
    # tell mediaconvert to combine clips
   
    return {
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json"
    },
    "body": event['body']
    }
